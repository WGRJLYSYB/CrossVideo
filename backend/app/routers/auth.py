from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from datetime import UTC, datetime, timedelta

from ..auth import create_access_token, hash_password, verify_password
from ..db import get_db
from ..models import User
from ..schemas import LoginRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.astimezone(UTC) if value.tzinfo is not None else value.replace(tzinfo=UTC)


@router.post("/register", status_code=status.HTTP_200_OK)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        payload.validate_confirmation()
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error

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


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
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
    return TokenResponse(access_token=create_access_token(user.id), username=user.username)
