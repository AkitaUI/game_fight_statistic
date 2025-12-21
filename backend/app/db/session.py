# app/db/session.py
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import DATABASE_URL
from app.core.config import settings

# Создаём sync-engine для SQLAlchemy 2.x
engine = create_engine(
    DATABASE_URL,
    future=True,
)

# Фабрика сессий для работы в коде и зависимостях FastAPI
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
    future=True
)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

get_session = get_db
