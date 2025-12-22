# app/db/repositories/base_repository.py
from __future__ import annotations

from typing import Generic, TypeVar, Type, Optional, List, Self

from sqlalchemy import select
from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Базовый репозиторий.

    Поддерживает "контекст игры" через self._game_id (опционально).
    Дочерние репозитории могут вызывать with_game(game_id) и учитывать это в запросах.
    """

    def __init__(self, session: Session, model: Optional[Type[T]] = None, game_id: int | None = None) -> None:
        self.session = session
        self.model = model
        self._game_id = game_id

    def with_game(self, game_id: int) -> Self:
        return self.__class__(self.session, game_id=game_id)  # type: ignore[misc]

    def require_game_id(self) -> int:
        if self._game_id is None:
            raise ValueError("game_id is required. Use .with_game(game_id) or pass game_id explicitly.")
        return self._game_id

    def add(self, entity: T) -> T:
        self.session.add(entity)
        return entity

    def delete(self, entity: T) -> None:
        self.session.delete(entity)

    def _apply_game_filter(self, stmt):
        """
        Если у модели есть поле game_id и в репозитории задан game_id — применяем фильтр.
        """
        if self._game_id is None or self.model is None:
            return stmt

        # Безопасно проверяем наличие атрибута game_id
        if hasattr(self.model, "game_id"):
            stmt = stmt.where(getattr(self.model, "game_id") == self._game_id)

        return stmt

    def get_by_id(self, entity_id: int) -> Optional[T]:
        if self.model is None:
            raise ValueError("Model is not set for BaseRepository")

        stmt = select(self.model).where(self.model.id == entity_id)
        stmt = self._apply_game_filter(stmt)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_all(self) -> List[T]:
        if self.model is None:
            raise ValueError("Model is not set for BaseRepository")

        stmt = select(self.model)
        stmt = self._apply_game_filter(stmt)
        return list(self.session.execute(stmt).scalars().all())
