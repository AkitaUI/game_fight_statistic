# app/db/models/dictionary.py

from __future__ import annotations

from typing import List, TYPE_CHECKING

from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .battle import Battle, WeaponStats


class Map(Base):
    __tablename__ = "maps"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Связи
    battles: Mapped[List["Battle"]] = relationship(
        back_populates="map",
    )


class GameMode(Base):
    __tablename__ = "game_modes"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    code: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Связи
    battles: Mapped[List["Battle"]] = relationship(
        back_populates="mode",
    )


class Weapon(Base):
    __tablename__ = "weapons"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Связи
    weapon_stats: Mapped[List["WeaponStats"]] = relationship(
        back_populates="weapon",
        cascade="all, delete-orphan",
    )
