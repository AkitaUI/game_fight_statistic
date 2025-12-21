# app/schemas/games.py
from __future__ import annotations

from pydantic import BaseModel


class GameRead(BaseModel):
    id: int
    slug: str
    name: str

    class Config:
        orm_mode = True
