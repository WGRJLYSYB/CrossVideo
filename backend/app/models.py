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

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
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
    progress: Mapped[list["PlaybackProgress"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    blocked_sites: Mapped[list["BlockedSite"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    watch_later: Mapped[list["WatchLater"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class PlaybackProgress(Base):
    __tablename__ = "playback_progress"
    __table_args__ = (Index("idx_user_url", "user_id", "url_hash", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
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


class BlockedSite(Base):
    __tablename__ = "blocked_sites"
    __table_args__ = (Index("idx_user_site", "user_id", "site_host", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    site_host: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp())
    user: Mapped[User] = relationship(back_populates="blocked_sites")


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
