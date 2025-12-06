# app/schemas/stats.py
from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from .base import ORMModel


class PlayerStatsFilter(ORMModel):
    """Фильтры для выборки статистики игрока."""
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    map_ids: Optional[List[int]] = None
    mode_ids: Optional[List[int]] = None
    ranked_only: Optional[bool] = None


class MapStatsItem(ORMModel):
    map_id: int
    map_name: str
    battles: int
    wins: int
    losses: int
    win_rate: float
    avg_kills: float
    avg_deaths: float
    avg_score: float


class WeaponStatsItem(ORMModel):
    weapon_id: int
    weapon_name: str
    kills: int
    headshots: int
    accuracy: float  # hits / shots_fired
    usage_count: int


class ModeStatsItem(ORMModel):
    mode_id: int
    mode_code: str
    mode_name: str
    battles: int
    avg_duration_seconds: float
    avg_score: float


class GlobalStatsFilter(ORMModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    ranked_only: Optional[bool] = None
