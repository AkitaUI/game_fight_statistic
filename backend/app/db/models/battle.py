# app/db/models/battle.py

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .dictionary import Map, GameMode, Weapon
    from .player import Player


class Battle(Base):
    __tablename__ = "battles"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    map_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("maps.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    mode_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("game_modes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    external_match_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    is_ranked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="FALSE",
    )

    # Связи
    map: Mapped[Optional["Map"]] = relationship(
        back_populates="battles",
    )

    mode: Mapped[Optional["GameMode"]] = relationship(
        back_populates="battles",
    )

    teams: Mapped[List["BattleTeam"]] = relationship(
        back_populates="battle",
        cascade="all, delete-orphan",
    )

    player_stats: Mapped[List["PlayerBattleStats"]] = relationship(
        back_populates="battle",
        cascade="all, delete-orphan",
    )


class BattleTeam(Base):
    __tablename__ = "battle_teams"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    battle_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("battles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    team_index: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )

    name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    is_winner: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )

    # Связи
    battle: Mapped["Battle"] = relationship(
        back_populates="teams",
    )

    player_stats: Mapped[List["PlayerBattleStats"]] = relationship(
        back_populates="team",
    )

    # Валидацию уникальности (battle_id, team_index) будем задавать через UniqueConstraint в миграции
    # либо через __table_args__ здесь, если нужно.
    __table_args__ = (
        # from sqlalchemy import UniqueConstraint
        # UniqueConstraint("battle_id", "team_index", name="uq_battle_team_index"),
    )
    

class PlayerBattleStats(Base):
    __tablename__ = "player_battle_stats"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    battle_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("battles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    player_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    team_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("battle_teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Статистика
    kills: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deaths: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assists: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    damage_dealt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    damage_taken: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    headshots: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # -1 = поражение, 0 = ничья, 1 = победа
    result: Mapped[Optional[int]] = mapped_column(
        SmallInteger,
        nullable=True,
    )

    joined_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    left_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Связи
    battle: Mapped["Battle"] = relationship(
        back_populates="player_stats",
    )

    player: Mapped["Player"] = relationship(
        back_populates="battle_stats",
    )

    team: Mapped[Optional["BattleTeam"]] = relationship(
        back_populates="player_stats",
    )

    weapon_stats: Mapped[List["WeaponStats"]] = relationship(
        back_populates="player_battle_stats",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        # Здесь можно добавить UniqueConstraint("battle_id", "player_id")
    )


class WeaponStats(Base):
    __tablename__ = "weapon_stats"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    player_battle_stats_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("player_battle_stats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    weapon_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("weapons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    shots_fired: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    kills: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    headshots: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Связи
    player_battle_stats: Mapped["PlayerBattleStats"] = relationship(
        back_populates="weapon_stats",
    )

    weapon: Mapped["Weapon"] = relationship(
        back_populates="weapon_stats",
    )

    __table_args__ = (
        # Здесь можно добавить UniqueConstraint("player_battle_stats_id", "weapon_id")
    )
