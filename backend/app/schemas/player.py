# app/schemas/player.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from .base import ORMModel


class PlayerBase(ORMModel):
    nickname: str


class PlayerCreate(PlayerBase):
    user_id: Optional[int] = None


class PlayerRead(PlayerBase):
    id: int
    game_id: int
    user_id: Optional[int] = None
    created_at: datetime


class PlayerListItem(PlayerRead):
    """Пока совпадает с PlayerRead."""
    pass


class PlayerStatsSummary(ORMModel):
    """Агрегированная статистика игрока."""
    player_id: int
    total_battles: int
    wins: int
    losses: int
    draws: int
    win_rate: float
    total_kills: int
    total_deaths: int
    total_assists: int
    avg_kd_ratio: float
    total_damage_dealt: int
    total_damage_taken: int
    avg_score: float


class PlayerWithStatsSummary(ORMModel):
    player: PlayerRead
    stats: PlayerStatsSummary
