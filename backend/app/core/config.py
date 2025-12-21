# app/core/config.py
from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str

    # Security
    SECRET_KEY: str = "_emGtl3MtaE8MsaMZFK2mPLMa_INqlRYgxAkoP8gBqJKwad125XPqF57h8jsVkyBMzf8HGFzcOoOyK15irRl2Q"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
