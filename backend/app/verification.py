# CrossVideo — Cross-platform video playback progress synchronization tool
# Copyright (C) 2026 WGRJLYSYB
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import base64
import hashlib
import html
import secrets
import smtplib
from datetime import UTC, datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path

import pyotp
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, status
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .models import CaptchaChallenge
from .schemas import CaptchaClick

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

CAPTCHA_WIDTH = 360
CAPTCHA_HEIGHT = 140
CAPTCHA_WORDS = ("movie", "story", "scene", "actor", "drama", "cinema", "frame", "star")
CAPTCHA_POINTS = ((60, 42), (180, 42), (300, 42), (60, 110), (180, 110), (300, 110))


def utc_datetime(value: datetime) -> datetime:
    return value.astimezone(UTC) if value.tzinfo is not None else value.replace(tzinfo=UTC)


def create_captcha(db: Session) -> dict[str, object]:
    db.query(CaptchaChallenge).filter(
        CaptchaChallenge.expires_at <= datetime.now(UTC),
    ).delete(synchronize_session=False)
    words = secrets.SystemRandom().sample(CAPTCHA_WORDS, len(CAPTCHA_POINTS))
    target_indexes = secrets.SystemRandom().sample(range(len(words)), 2)
    target_points = [
        {"x": float(CAPTCHA_POINTS[index][0]), "y": float(CAPTCHA_POINTS[index][1])}
        for index in target_indexes
    ]

    text = "".join(
        f'<text x="{x}" y="{y + 6}" text-anchor="middle" '
        f'transform="rotate({secrets.randbelow(25) - 12} {x} {y})">{html.escape(word)}</text>'
        for word, (x, y) in zip(words, CAPTCHA_POINTS)
    )
    noise = "".join(
        f'<circle cx="{secrets.randbelow(CAPTCHA_WIDTH)}" cy="{secrets.randbelow(CAPTCHA_HEIGHT)}" '
        f'r="{1 + secrets.randbelow(3)}" fill="#{secrets.choice(("ac8178", "748b9c", "a6a18b"))}"/>'
        for _ in range(35)
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CAPTCHA_WIDTH}" height="{CAPTCHA_HEIGHT}" '
        f'viewBox="0 0 {CAPTCHA_WIDTH} {CAPTCHA_HEIGHT}"><rect width="100%" height="100%" fill="#f3efe6"/>'
        f'{noise}<g fill="#283444" font-family="sans-serif" font-size="17" font-weight="600">{text}</g></svg>'
    )
    challenge_id = secrets.token_urlsafe(32)
    db.add(CaptchaChallenge(
        id=challenge_id,
        target_points=target_points,
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    ))
    db.commit()
    return {
        "challenge_id": challenge_id,
        "image": "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii"),
        "sequence": [words[index] for index in target_indexes],
        "width": CAPTCHA_WIDTH,
        "height": CAPTCHA_HEIGHT,
    }


def verify_captcha(db: Session, challenge_id: str, clicks: list[CaptchaClick]) -> None:
    challenge = db.scalar(
        select(CaptchaChallenge)
        .where(CaptchaChallenge.id == challenge_id)
        .with_for_update()
    )
    if challenge is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="captcha expired or invalid")

    expected_points = challenge.target_points
    expired = utc_datetime(challenge.expires_at) <= datetime.now(UTC)
    valid = len(clicks) == len(expected_points) and not expired
    if valid:
        valid = all(
            abs(click.x - expected["x"]) <= 48 and abs(click.y - expected["y"]) <= 22
            for click, expected in zip(clicks, expected_points)
        )

    db.delete(challenge)
    db.commit()
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="captcha expired or invalid")


def new_action_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    return token, hashlib.sha256(token.encode("utf-8")).hexdigest()


def encrypt_totp_secret(secret: str) -> str:
    key = base64.urlsafe_b64encode(hashlib.sha256(get_settings().secret_key.encode("utf-8")).digest())
    return Fernet(key).encrypt(secret.encode("utf-8")).decode("ascii")


def decrypt_totp_secret(encrypted_secret: str) -> str:
    key = base64.urlsafe_b64encode(hashlib.sha256(get_settings().secret_key.encode("utf-8")).digest())
    return Fernet(key).decrypt(encrypted_secret.encode("ascii")).decode("utf-8")


def render_email_template(template_name: str, link: str) -> str:
    return templates.get_template(template_name).render(link=link)


def send_action_email(recipient: str, subject: str, action_path: str, token: str, template_name: str) -> None:
    settings = get_settings()
    if not settings.smtp_host or not settings.smtp_from_email:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="email delivery is not configured",
        )

    link = f"{settings.frontend_base_url.rstrip('/')}/{action_path}?token={token}"
    html_body = render_email_template(template_name, link)

    message = MIMEText(html_body, "html", "utf-8")
    message["Subject"] = subject
    message["From"] = settings.smtp_from_email
    message["To"] = recipient

    with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)


def verify_totp(encrypted_secret: str | None, code: str) -> bool:
    if not encrypted_secret or not code.isdigit():
        return False
    try:
        return pyotp.TOTP(decrypt_totp_secret(encrypted_secret)).verify(code, valid_window=1)
    except (InvalidToken, ValueError, TypeError):
        return False
