# CrossVideo — Cross-platform video playback progress synchronization tool
# Copyright (C) 2026 WGRJLYSYB
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import hashlib
from datetime import UTC, datetime, timedelta

import pyotp
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..auth import (
    create_access_token,
    create_two_factor_challenge,
    decode_two_factor_challenge,
    get_current_user,
    hash_password,
    verify_password,
)
from ..db import get_db
from ..models import EmailActionToken, Favorite, PlaybackProgress, User, WatchLater
from ..schemas import (
    AdminUserInfoResponse,
    EmailRequest,
    EmailTokenRequest,
    LoginRequest,
    LoginResponse,
    PasswordChangeRequest,
    PasswordResetRequest,
    RegisterRequest,
    TokenResponse,
    TotpCodeRequest,
    TotpDisableRequest,
    TwoFactorLoginRequest,
)
from ..verification import (
    create_captcha,
    decrypt_totp_secret,
    encrypt_totp_secret,
    new_action_token,
    send_action_email,
    utc_datetime,
    verify_captcha,
    verify_totp,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.astimezone(UTC) if value.tzinfo is not None else value.replace(tzinfo=UTC)


@router.get("/captcha")
def issue_captcha(db: Session = Depends(get_db)) -> dict[str, object]:
    return create_captcha(db)


@router.post("/register", status_code=status.HTTP_200_OK)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    verify_captcha(db, payload.captcha_id, payload.captcha_clicks)
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="passwords do not match")
    if db.scalar(select(User).where(User.username == payload.username)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username already exists")

    user = User(username=payload.username, hashed_password=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username already exists") from None
    return {"message": "User registered successfully"}


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    verify_captcha(db, payload.captcha_id, payload.captcha_clicks)
    user = db.scalar(select(User).where(User.username == payload.username))
    now = datetime.now(UTC)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    locked_until = as_utc(user.locked_until)
    if locked_until and locked_until > now:
        retry_after = int((locked_until - now).total_seconds()) + 1
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"too many login attempts; retry in {retry_after} seconds", headers={"Retry-After": str(retry_after)})
    if not verify_password(payload.password, user.hashed_password):
        user.failed_login_attempts += 1
        delay = min(60, 2 ** max(0, user.failed_login_attempts - 1))
        user.locked_until = now + timedelta(seconds=delay)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"incorrect username or password; retry in {delay} seconds", headers={"Retry-After": str(delay), "WWW-Authenticate": "Bearer"})
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
    if user.totp_enabled:
        return LoginResponse(
            username=user.username,
            requires_2fa=True,
            challenge_token=create_two_factor_challenge(user.id),
        )
    return LoginResponse(access_token=create_access_token(user.id), username=user.username)


@router.post("/login/2fa", response_model=TokenResponse)
def complete_two_factor_login(payload: TwoFactorLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        user_id = decode_two_factor_challenge(payload.challenge_token)
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired two-factor challenge") from None

    user = db.get(User, user_id)
    if user is None or not user.totp_enabled or not verify_totp(user.totp_secret, payload.code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid authenticator code")
    return TokenResponse(access_token=create_access_token(user.id), username=user.username)


@router.get("/me", response_model=AdminUserInfoResponse)
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AdminUserInfoResponse:
    return AdminUserInfoResponse(
        id=user.id,
        username=user.username,
        created_at=as_utc(user.created_at),
        history_count=db.scalar(select(func.count(PlaybackProgress.id)).where(PlaybackProgress.user_id == user.id)) or 0,
        favorites_count=db.scalar(select(func.count(Favorite.id)).where(Favorite.user_id == user.id)) or 0,
        watch_later_count=db.scalar(select(func.count(WatchLater.id)).where(WatchLater.user_id == user.id)) or 0,
    )


@router.get("/settings")
def get_account_settings(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    pending = db.scalar(
        select(EmailActionToken)
        .where(
            EmailActionToken.user_id == user.id,
            EmailActionToken.purpose == "verify_email",
            EmailActionToken.used_at.is_(None),
            EmailActionToken.expires_at > datetime.now(UTC),
        )
        .order_by(EmailActionToken.id.desc())
        .limit(1)
    )
    return {
        "email": user.email,
        "email_verified": user.email_verified,
        "pending_email": pending.target_email if pending is not None else None,
        "two_factor_enabled": user.totp_enabled,
    }


@router.post("/password")
def change_password(payload: PasswordChangeRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="passwords do not match")
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="current password is incorrect")
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"message": "password updated"}


@router.post("/email")
def request_email_verification(payload: EmailRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    email = str(payload.email).strip().lower()
    if db.scalar(select(User.id).where(User.email == email, User.id != user.id)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email is already bound to another account")
    if user.email == email and user.email_verified:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email is already verified for this account")

    db.query(EmailActionToken).filter(
        EmailActionToken.user_id == user.id,
        EmailActionToken.purpose == "verify_email",
        EmailActionToken.used_at.is_(None),
    ).delete(synchronize_session=False)
    token, token_hash = new_action_token()
    db.add(EmailActionToken(
        user_id=user.id,
        token_hash=token_hash,
        purpose="verify_email",
        target_email=email,
        expires_at=datetime.now(UTC) + timedelta(hours=24),
    ))
    send_action_email(email, "CrossVideo 邮箱验证", "verify-email", token, "email_verify.html")
    db.commit()
    return {"message": "verification email sent"}


@router.post("/email/confirm")
def confirm_email(payload: EmailTokenRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    token_hash = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()
    record = db.scalar(select(EmailActionToken).where(EmailActionToken.token_hash == token_hash).with_for_update())
    if (
        record is None
        or record.purpose != "verify_email"
        or record.used_at is not None
        or utc_datetime(record.expires_at) <= datetime.now(UTC)
        or record.target_email is None
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email verification link is invalid or expired")
    if db.scalar(select(User.id).where(User.email == record.target_email, User.id != record.user_id)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email is already bound to another account")

    user = db.get(User, record.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email verification link is invalid or expired")
    user.email = record.target_email
    user.email_verified = True
    record.used_at = datetime.now(UTC)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email is already bound to another account") from None
    return {"message": "email verified"}


@router.post("/password-reset/request")
def request_password_reset(payload: EmailRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    email = str(payload.email).strip().lower()
    user = db.scalar(select(User).where(User.email == email, User.email_verified.is_(True)))
    if user is not None:
        db.query(EmailActionToken).filter(
            EmailActionToken.user_id == user.id,
            EmailActionToken.purpose == "reset_password",
            EmailActionToken.used_at.is_(None),
        ).delete(synchronize_session=False)
        token, token_hash = new_action_token()
        db.add(EmailActionToken(
            user_id=user.id,
            token_hash=token_hash,
            purpose="reset_password",
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
        ))
        send_action_email(email, "CrossVideo 密码重置", "reset-password", token, "email_reset_password.html")
        db.commit()
    return {"message": "if the verified email exists, a reset link has been sent"}


@router.post("/password-reset/confirm")
def confirm_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="passwords do not match")
    token_hash = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()
    record = db.scalar(select(EmailActionToken).where(EmailActionToken.token_hash == token_hash).with_for_update())
    if (
        record is None
        or record.purpose != "reset_password"
        or record.used_at is not None
        or utc_datetime(record.expires_at) <= datetime.now(UTC)
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="password reset link is invalid or expired")
    user = db.get(User, record.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="password reset link is invalid or expired")
    user.hashed_password = hash_password(payload.new_password)
    record.used_at = datetime.now(UTC)
    db.commit()
    return {"message": "password reset"}


@router.post("/2fa/setup")
def setup_two_factor(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    if user.totp_enabled:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="two-factor authentication is already enabled")
    secret = pyotp.random_base32()
    user.totp_secret = encrypt_totp_secret(secret)
    db.commit()
    uri = pyotp.TOTP(secret).provisioning_uri(name=user.username, issuer_name="CrossVideo")
    return {"secret": secret, "provisioning_uri": uri}


@router.post("/2fa/enable")
def enable_two_factor(payload: TotpCodeRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    if user.totp_enabled or not verify_totp(user.totp_secret, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="authenticator code is invalid")
    user.totp_enabled = True
    db.commit()
    return {"message": "two-factor authentication enabled"}


@router.post("/2fa/disable")
def disable_two_factor(payload: TotpDisableRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    if not user.totp_enabled or not verify_password(payload.password, user.hashed_password) or not verify_totp(user.totp_secret, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="password or authenticator code is incorrect")
    user.totp_enabled = False
    user.totp_secret = None
    db.commit()
    return {"message": "two-factor authentication disabled"}
