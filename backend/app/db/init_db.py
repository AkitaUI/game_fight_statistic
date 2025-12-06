# app/db/init_db.py
from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.base import Base  # Base = DeclarativeBase
from app.db.session import engine, SessionLocal
from app.db.models import user, player, dictionary, battle  # noqa: F401


def init_db() -> None:
    
    # Импорты моделей выше нужны, чтобы все таблицы были зарегистрированы в Base.metadata
    Base.metadata.create_all(bind=engine)


def get_db_session() -> Session:
    
    return SessionLocal()
