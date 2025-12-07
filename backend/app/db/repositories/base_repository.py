# app/db/repositories/base_repository.py
from __future__ import annotations

from typing import Generic, TypeVar, Type, Optional, List

from sqlalchemy import select
from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Базовый репозиторий.

    Даёт:
      - self.session — сессия SQLAlchemy
      - простые методы add / delete / get_by_id / list_all (если задан model)
    """

    def __init__(self, session: Session, model: Optional[Type[T]] = None) -> None:
        self.session = session
        self.model = model

    def add(self, entity: T) -> T:
        self.session.add(entity)
        return entity

    def delete(self, entity: T) -> None:
        self.session.delete(entity)

    def get_by_id(self, entity_id: int) -> Optional[T]:
        """
        Универсальный get_by_id, если в модель передан класс ORM с полем id.
        """
        if self.model is None:
            raise ValueError("Model is not set for BaseRepository")

        stmt = select(self.model).where(self.model.id == entity_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_all(self) -> List[T]:
        """
        Вернуть все записи, если задана модель.
        """
        if self.model is None:
            raise ValueError("Model is not set for BaseRepository")

        stmt = select(self.model)
        return self.session.execute(stmt).scalars().all()
