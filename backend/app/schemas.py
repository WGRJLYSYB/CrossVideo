from datetime import datetime

from pydantic import BaseModel, Field, field_validator


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


class ProgressListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ProgressItem]
