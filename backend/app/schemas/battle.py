# app/schemas/battle.py
from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import Field

from .base import ORMModel


class BattleTeamBase(ORMModel):
    team_index: int
    name: Optional[str] = None


class BattleTeamCreate(BattleTeamBase):
    is_winner: Optional[bool] = None


class BattleTeamRead(BattleTeamBase):
    id: int
    battle_id: int
    is_winner: Optional[bool] = None


class WeaponStatsItem(ORMModel):
    weapon_id: int
    shots_fired: int
    hits: int
    kills: int
    headshots: int


class PlayerBattleStatsBase(ORMModel):
    player_id: int
    team_id: Optional[int] = None

    kills: int = 0
    deaths: int = 0
    assists: int = 0
    damage_dealt: int = 0
    damage_taken: int = 0
    score: int = 0
    headshots: int = 0

    result: Optional[int] = None  # -1, 0, 1
    joined_at: Optional[datetime] = None
    left_at: Optional[datetime] = None


class PlayerBattleStatsCreate(PlayerBattleStatsBase):
    weapon_stats: Optional[List[WeaponStatsItem]] = None


class PlayerBattleStatsRead(PlayerBattleStatsBase):
    id: int
    battle_id: int
    weapon_stats: List[WeaponStatsItem] = Field(default_factory=list)


class BattleBase(ORMModel):
    map_id: Optional[int] = None
    mode_id: Optional[int] = None
    is_ranked: bool = False
    started_at: Optional[datetime] = None
    external_match_id: Optional[str] = None


class BattleCreate(BattleBase):
    """Создание боя."""
    pass


class BattleRead(BattleBase):
    id: int
    created_at: datetime
    ended_at: Optional[datetime] = None

    teams: List[BattleTeamRead] = Field(default_factory=list)
    player_stats: List[PlayerBattleStatsRead] = Field(default_factory=list)


class BattleListItem(ORMModel):
    id: int
    map_id: Optional[int] = None
    mode_id: Optional[int] = None
    is_ranked: bool
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime


class BattleFinishRequest(ORMModel):
    ended_at: Optional[datetime] = None
