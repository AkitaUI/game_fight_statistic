# app/schemas/auth.py
from __future__ import annotations

from pydantic import Field, BaseModel
from app.db.models.user import UserRole

from .base import ORMModel


class Token(ORMModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class UserRegister(ORMModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=72)


class UserPublic(ORMModel):
    id: int
    username: str
    role: UserRole
    
    class Config:
        from_attributes = True  # pydantic v2
