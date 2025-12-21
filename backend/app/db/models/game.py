# app/db/models/game.py
from __future__ import annotations

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)

    # relationships
    battles = relationship("Battle", back_populates="game", cascade="all, delete-orphan")
    players = relationship("Player", back_populates="game", cascade="all, delete-orphan")

    # NEW: справочники по игре
    maps = relationship("Map", back_populates="game", cascade="all, delete-orphan")
    modes = relationship("GameMode", back_populates="game", cascade="all, delete-orphan")
    weapons = relationship("Weapon", back_populates="game", cascade="all, delete-orphan")
