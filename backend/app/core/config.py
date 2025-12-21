# app/core/config.py
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # DB
    DATABASE_URL: str = ""

    # Security
    SECRET_KEY: str = "_emGtl3MtaE8MsaMZFK2mPLMa_INqlRYgxAkoP8gBqJKwad125XPqF57h8jsVkyBMzf8HGFzcOoOyK15irRl2Q"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()

# backward-compatible exports (чтобы не падали импорты из старых файлов)
DATABASE_URL = settings.DATABASE_URL
