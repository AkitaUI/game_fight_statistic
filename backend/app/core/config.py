from __future__ import annotations

import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://user:password@localhost:5432/game_stats"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
DATABASE_URL = settings.DATABASE_URL
