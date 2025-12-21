# app/db/repositories/base_repository.py
from __future__ import annotations

from typing import Generic, TypeVar, Type, Optional, List, Any

from sqlalchemy import select
from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Базовый репозиторий.

    Даёт:
      - self.session — сессия SQLAlchemy
      - self.model — класс модели (если задан)
      - self.game_id — контекст игры (если нужен)
    """

    def __init__(
        self,
        session: Session,
        model: Optional[Type[T]] = None,
        game_id: Optional[int] = None,
    ) -> None:
        self.session = session
        self.model = model
        self.game_id = game_id

    def with_game(self, game_id: int) -> "BaseRepository[T]":
        """Вернуть тот же репозиторий, но с выставленным game_id."""
        self.game_id = game_id
        return self

    def require_game_id(self) -> int:
        if self.game_id is None:
            raise ValueError("game_id is required for this operation")
        return self.game_id

    def add(self, entity: T) -> T:
        self.session.add(entity)
        return entity

    def delete(self, entity: T) -> None:
        self.session.delete(entity)

    def get_by_id(self, entity_id: int) -> Optional[T]:
        """
        Универсальный get_by_id.
        Если модель имеет колонку game_id и self.game_id задан — добавим фильтр game_id.
        """
        if self.model is None:
            raise ValueError("Model is not set for BaseRepository")

        stmt = select(self.model).where(self.model.id == entity_id)

        # если у модели есть game_id — ограничиваем выборку
        if self.game_id is not None and hasattr(self.model, "game_id"):
            stmt = stmt.where(getattr(self.model, "game_id") == self.game_id)

        return self.session.execute(stmt).scalar_one_or_none()

    def list_all(self) -> List[T]:
        """
        Вернуть все записи, если задана модель.
        Если модель имеет game_id и self.game_id задан — фильтруем по game_id.
        """
        if self.model is None:
            raise ValueError("Model is not set for BaseRepository")

        stmt = select(self.model)
        if self.game_id is not None and hasattr(self.model, "game_id"):
            stmt = stmt.where(getattr(self.model, "game_id") == self.game_id)

        return list(self.session.execute(stmt).scalars().all())
