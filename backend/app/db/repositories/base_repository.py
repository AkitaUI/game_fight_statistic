# app/db/repositories/base_repository.py

from abc import ABC
from typing import Generic, TypeVar

from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    Базовый репозиторий: держит ссылку на Session.
    Конкретные репозитории добавляют методы над своей моделью.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        return self._session
