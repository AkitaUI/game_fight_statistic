# app/schemas/base.py
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class ORMModel(BaseModel):
    """Базовая схема с поддержкой работы из ORM-моделей."""
    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class PagedResponse(ORMModel):
    total: int
    items: list
