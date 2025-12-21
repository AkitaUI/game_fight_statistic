# app/db/init_db.py
from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine, SessionLocal

# Важно: импорт моделей, чтобы они зарегистрировались в Base.metadata
from app.db import models  # noqa: F401


def init_db() -> None:
    """Создаёт таблицы (обычно для dev). В проде лучше использовать alembic."""
    Base.metadata.create_all(bind=engine)


def get_db_session() -> Session:
    """Совместимость со старым кодом (если где-то вызывается напрямую)."""
    return SessionLocal()
