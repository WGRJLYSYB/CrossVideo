# CrossVideo — Cross‑platform video playback progress synchronization tool
# Copyright (C) 2026 WGRJLYSYB
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    email: Mapped[str | None] = mapped_column(String(320), unique=True, index=True, nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    totp_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    progress: Mapped[list["PlaybackProgress"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    media_progress: Mapped[list["MediaProgress"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    blocked_sites: Mapped[list["BlockedSite"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    site_visits: Mapped[list["UserSite"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    watch_later: Mapped[list["WatchLater"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class PlaybackProgress(Base):
    __tablename__ = "playback_progress"
    __table_args__ = (Index("idx_user_url", "user_id", "url_hash", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    media_progress_id: Mapped[int | None] = mapped_column(
        ForeignKey("media_progress.id", ondelete="SET NULL", name="fk_playback_progress_media_progress_id"),
        nullable=True,
        index=True,
    )
    site_host: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    url_hash: Mapped[str] = mapped_column(String(64))
    clean_url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    progress_seconds: Mapped[float] = mapped_column(Float)
    duration: Mapped[float] = mapped_column(Float)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    client_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    user: Mapped[User] = relationship(back_populates="progress")
    media_progress: Mapped["MediaProgress | None"] = relationship(back_populates="url_progress")


class MediaProgress(Base):
    __tablename__ = "media_progress"
    __table_args__ = (
        Index("idx_media_user_title_season_episode", "user_id", "title_key", "season", "episode", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(1000))
    title_key: Mapped[str] = mapped_column(String(64))
    season: Mapped[int] = mapped_column(Integer)
    episode: Mapped[int] = mapped_column(Integer)
    last_url_hash: Mapped[str] = mapped_column(String(64))
    progress_seconds: Mapped[float] = mapped_column(Float)
    duration: Mapped[float] = mapped_column(Float)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    client_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    user: Mapped[User] = relationship(back_populates="media_progress")
    url_progress: Mapped[list[PlaybackProgress]] = relationship(back_populates="media_progress")


class BlockedSite(Base):
    __tablename__ = "blocked_sites"
    __table_args__ = (Index("idx_user_site", "user_id", "site_host", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    site_host: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp())
    user: Mapped[User] = relationship(back_populates="blocked_sites")


class UserSite(Base):
    __tablename__ = "user_sites"
    __table_args__ = (Index("idx_user_site_host", "user_id", "site_host", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    site_host: Mapped[str] = mapped_column(String(255))
    site_name: Mapped[str] = mapped_column(String(255))
    last_watched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    watched_seconds: Mapped[float] = mapped_column(Float, default=0.0, server_default="0")
    title_fetch_attempted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    user: Mapped[User] = relationship(back_populates="site_visits")


class CaptchaChallenge(Base):
    __tablename__ = "captcha_challenges"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    target_points: Mapped[list[dict[str, float]]] = mapped_column(JSON)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class EmailActionToken(Base):
    __tablename__ = "email_action_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    purpose: Mapped[str] = mapped_column(String(32))
    target_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EmailSendAttempt(Base):
    __tablename__ = "email_send_attempts"
    __table_args__ = (Index("idx_email_send_user_purpose_sent", "user_id", "purpose", "sent_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    purpose: Mapped[str] = mapped_column(String(32))
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp())


class AIConversation(Base):
    __tablename__ = "ai_conversations"
    __table_args__ = (Index("idx_ai_conversation_user", "user_id", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    messages: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class AIMonthlyUsage(Base):
    __tablename__ = "ai_monthly_usage"
    __table_args__ = (Index("idx_ai_usage_user_month", "user_id", "month", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    month: Mapped[str] = mapped_column(String(7))
    used_tokens: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    reserved_tokens: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (Index("idx_fav_user_url", "user_id", "url_hash", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    site_host: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    url_hash: Mapped[str] = mapped_column(String(64))
    clean_url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    duration: Mapped[float] = mapped_column(Float, default=0.0, server_default="0")
    progress_seconds: Mapped[float] = mapped_column(Float, default=0.0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    user: Mapped[User] = relationship(back_populates="favorites")


class WatchLater(Base):
    __tablename__ = "watch_later"
    __table_args__ = (Index("idx_wl_user_url", "user_id", "url_hash", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    site_host: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    url_hash: Mapped[str] = mapped_column(String(64))
    clean_url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    duration: Mapped[float] = mapped_column(Float, default=0.0, server_default="0")
    progress_seconds: Mapped[float] = mapped_column(Float, default=0.0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    user: Mapped[User] = relationship(back_populates="watch_later")
