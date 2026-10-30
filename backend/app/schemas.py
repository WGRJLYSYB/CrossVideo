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

from pydantic import BaseModel, Field, field_validator
from urllib.parse import urlparse


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^\S+$")
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_has_letters_and_numbers(cls, value: str) -> str:
        if not any(char.isalpha() for char in value) or not any(char.isdigit() for char in value):
            raise ValueError("password must contain both letters and numbers")
        return value

    def validate_confirmation(self) -> None:
        if self.password != self.confirm_password:
            raise ValueError("passwords do not match")


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^\S+$")
    password: str = Field(min_length=1, max_length=128)


class SiteRequest(BaseModel):
    site_host: str = Field(min_length=1, max_length=255, pattern=r"^[A-Za-z0-9.-]+$")

    @field_validator("site_host", mode="before")
    @classmethod
    def normalize_site_host(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("site_host must be a string")
        host = value.strip()
        if "://" in host or host.startswith("//"):
            parsed = urlparse(host if "://" in host else f"https:{host}")
            host = parsed.hostname or ""
        return host.rstrip(".").lower()


class BulkDeleteRequest(BaseModel):
    ids: list[int] = Field(min_length=1, max_length=50)


class SiteInfo(BaseModel):
    site_host: str
    site_name: str
    last_watched_at: datetime


class DashboardSiteStat(BaseModel):
    site_host: str
    site_name: str
    video_count: int
    watched_seconds: float


class ActiveVideoInfo(BaseModel):
    client_id: str
    site_host: str | None = None
    title: str
    play_started_at: datetime | None = None


class DashboardResponse(BaseModel):
    online_device_count: int
    current_videos: list[ActiveVideoInfo]
    sites: list[DashboardSiteStat]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class ProgressSyncRequest(BaseModel):
    url_hash: str = Field(min_length=64, max_length=64, pattern=r"^[a-fA-F0-9]{64}$")
    clean_url: str = Field(min_length=1, max_length=4096)
    title: str = Field(min_length=1, max_length=1000)
    progress_seconds: float = Field(ge=0)
    duration: float = Field(gt=0)
    client_updated_at: datetime | None = None
    site_host: str = Field(min_length=1, max_length=255, pattern=r"^[A-Za-z0-9.-]+$")


class ProgressQueryResponse(BaseModel):
    found: bool
    progress_seconds: float | None = None
    duration: float | None = None
    updated_at: datetime | None = None


class ProgressItem(BaseModel):
    id: int
    clean_url: str
    title: str
    progress_seconds: float
    duration: float
    updated_at: datetime
    completed: bool


class ProgressListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ProgressItem]


# --- Admin Dashboard Schemas ---

class AdminUserInfoResponse(BaseModel):
    id: int
    username: str
    created_at: datetime | None = None
    history_count: int = 0
    favorites_count: int = 0
    watch_later_count: int = 0


class AdminHistoryItem(BaseModel):
    id: int
    site_host: str | None = None
    clean_url: str
    title: str
    progress_seconds: float
    duration: float
    completed: bool
    updated_at: datetime | None = None
    is_favorite: bool = False
    is_watch_later: bool = False


class AdminHistoryListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AdminHistoryItem]


class FavoriteCreateRequest(BaseModel):
    clean_url: str = Field(min_length=1, max_length=4096)
    title: str = Field(min_length=1, max_length=1000)
    site_host: str | None = Field(default=None, max_length=255)
    duration: float = Field(default=0.0, ge=0)
    progress_seconds: float = Field(default=0.0, ge=0)


class FavoriteItem(BaseModel):
    id: int
    site_host: str | None = None
    clean_url: str
    title: str
    duration: float
    progress_seconds: float
    created_at: datetime | None = None
    is_watch_later: bool = False


class FavoriteListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[FavoriteItem]


class WatchLaterCreateRequest(BaseModel):
    clean_url: str = Field(min_length=1, max_length=4096)
    title: str = Field(min_length=1, max_length=1000)
    site_host: str | None = Field(default=None, max_length=255)
    duration: float = Field(default=0.0, ge=0)
    progress_seconds: float = Field(default=0.0, ge=0)


class WatchLaterItem(BaseModel):
    id: int
    site_host: str | None = None
    clean_url: str
    title: str
    duration: float
    progress_seconds: float
    created_at: datetime | None = None
    is_favorite: bool = False


class WatchLaterListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[WatchLaterItem]
