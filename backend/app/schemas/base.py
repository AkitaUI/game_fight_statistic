# app/schemas/base.py
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ORMModel(BaseModel):
    """Базовая схема с поддержкой работы из ORM-моделей (Pydantic v2)."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class PagedResponse(ORMModel, Generic[T]):
    total: int
    items: list[T]
