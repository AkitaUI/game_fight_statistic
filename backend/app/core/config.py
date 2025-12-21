# app/core/config.py
from __future__ import annotations

import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "_emGtl3MtaE8MsaMZFK2mPLMa_INqlRYgxAkoP8gBqJKwad125XPqF57h8jsVkyBMzf8HGFzcOoOyK15irRl2Q")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

