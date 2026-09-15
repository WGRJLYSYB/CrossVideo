from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    progress: Mapped[list["PlaybackProgress"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    blocked_sites: Mapped[list["BlockedSite"]] = relationship(back_populates="user", cascade="all, delete-orphan")


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
    client_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    user: Mapped[User] = relationship(back_populates="progress")


class BlockedSite(Base):
    __tablename__ = "blocked_sites"
    __table_args__ = (Index("idx_user_site", "user_id", "site_host", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    site_host: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
    user: Mapped[User] = relationship(back_populates="blocked_sites")
