# app/schemas/battle.py
from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from .base import ORMModel


# --- Вложенные DTO ---


class BattleTeamBase(ORMModel):
    team_index: int
    name: str


class BattleTeamCreate(BattleTeamBase):
    is_winner: bool = False


class BattleTeamRead(BattleTeamBase):
    id: int
    battle_id: int
    is_winner: bool


class WeaponStatsItem(ORMModel):
    weapon_id: int
    shots_fired: int
    hits: int
    kills: int
    headshots: int


class PlayerBattleStatsBase(ORMModel):
    player_id: int
    team_id: int
    kills: int
    deaths: int
    assists: int
    damage_dealt: int
    damage_taken: int
    score: int
    headshots: int
    result: int  # -1, 0, 1
    joined_at: Optional[datetime] = None
    left_at: Optional[datetime] = None


class PlayerBattleStatsCreate(PlayerBattleStatsBase):
    weapon_stats: Optional[List[WeaponStatsItem]] = None


class PlayerBattleStatsRead(PlayerBattleStatsBase):
    id: int
    battle_id: int
    weapon_stats: List[WeaponStatsItem] = []


# --- Бой ---


class BattleBase(ORMModel):
    map_id: int
    mode_id: int
    is_ranked: bool = False
    started_at: Optional[datetime] = None
    external_match_id: Optional[str] = None


class BattleCreate(BattleBase):
    """Создание боя. Команды и участники можно добавлять позже отдельными вызовами."""
    pass


class BattleRead(BattleBase):
    id: int
    created_at: datetime
    ended_at: Optional[datetime] = None

    teams: List[BattleTeamRead] = []
    players_stats: List[PlayerBattleStatsRead] = []


class BattleListItem(ORMModel):
    id: int
    map_id: int
    mode_id: int
    is_ranked: bool
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    created_at: datetime


class BattleFinishRequest(ORMModel):
    ended_at: Optional[datetime] = None  # если не указано — возьмём now() на уровне сервиса
