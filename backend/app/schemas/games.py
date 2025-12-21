# app/schemas/games.py
from __future__ import annotations

from .base import ORMModel


class GameRead(ORMModel):
    id: int
    slug: str
    name: str
