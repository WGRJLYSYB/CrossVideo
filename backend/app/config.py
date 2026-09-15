from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CrossVideo Progress API"
    secret_key: str = "change-this-secret-key-in-production"
    access_token_expire_minutes: int = 60 * 24 * 30
    database_url: str = "sqlite:///./crossvideo.db"
    cors_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", env_prefix="CROSSVIDEO_", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
