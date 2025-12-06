# app/db/base.py
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""
    pass


from app.db.models import user, player, dictionary, battle  # noqa: F401
