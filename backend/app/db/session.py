# app/db/session.py
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import DATABASE_URL

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
)


def get_session() -> Generator[Session, None, None]:
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
