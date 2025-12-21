# app/schemas/auth.py
from __future__ import annotations

from pydantic import Field

from .base import ORMModel


class Token(ORMModel):
    access_token: str
    token_type: str = "bearer"


class UserRegister(ORMModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class UserPublic(ORMModel):
    id: int
    username: str
    role: str
