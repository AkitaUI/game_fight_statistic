# app/db/models/dictionary.py
from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import BigInteger, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .battle import Battle, WeaponStats
    from .game import Game


class Map(Base):
    __tablename__ = "maps"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # NEW: изоляция справочников по игре
    game_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Связи
    game: Mapped["Game"] = relationship(back_populates="maps")

    battles: Mapped[List["Battle"]] = relationship(back_populates="map")

    __table_args__ = (
        UniqueConstraint("game_id", "name", name="uq_maps_game_id_name"),
    )


class GameMode(Base):
    __tablename__ = "game_modes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # NEW: изоляция справочников по игре
    game_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Связи
    game: Mapped["Game"] = relationship(back_populates="modes")

    battles: Mapped[List["Battle"]] = relationship(back_populates="mode")

    __table_args__ = (
        UniqueConstraint("game_id", "code", name="uq_game_modes_game_id_code"),
    )


class Weapon(Base):
    __tablename__ = "weapons"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # NEW: изоляция справочников по игре
    game_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Связи
    game: Mapped["Game"] = relationship(back_populates="weapons")

    weapon_stats: Mapped[List["WeaponStats"]] = relationship(
        back_populates="weapon",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("game_id", "name", name="uq_weapons_game_id_name"),
    )
