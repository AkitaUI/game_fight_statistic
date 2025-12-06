# app/services/stats_service.py
from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.core.exceptions import PlayerNotFoundError
from app.db.repositories.player_repository import PlayerRepository
from app.db.repositories.stats_repository import StatsRepository
from app.schemas.player import PlayerStatsSummary
from app.schemas.stats import (
    PlayerStatsFilter,
    MapStatsItem,
    WeaponStatsItem,
    ModeStatsItem,
    GlobalStatsFilter,
)


class StatsService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.player_repo = PlayerRepository(session)
        self.stats_repo = StatsRepository(session)

    # --- Статистика по игроку ---

    def get_player_summary(self, player_id: int, filters: PlayerStatsFilter) -> PlayerStatsSummary:
        player = self.player_repo.get_by_id(player_id)
        if player is None:
            raise PlayerNotFoundError(f"Player with id={player_id} not found")

        raw = self.stats_repo.get_player_stats_summary(
            player_id=player_id,
            date_from=filters.date_from,
            date_to=filters.date_to,
            map_ids=filters.map_ids,
            mode_ids=filters.mode_ids,
            ranked_only=filters.ranked_only,
        )
        return PlayerStatsSummary(**raw)

    def get_player_map_stats(self, player_id: int, filters: PlayerStatsFilter) -> List[MapStatsItem]:
        player = self.player_repo.get_by_id(player_id)
        if player is None:
            raise PlayerNotFoundError(f"Player with id={player_id} not found")

        rows = self.stats_repo.get_player_stats_by_map(
            player_id=player_id,
            date_from=filters.date_from,
            date_to=filters.date_to,
            map_ids=filters.map_ids,
            mode_ids=filters.mode_ids,
            ranked_only=filters.ranked_only,
        )
        return [MapStatsItem(**row) for row in rows]

    def get_player_weapon_stats(
        self,
        player_id: int,
        filters: PlayerStatsFilter,
    ) -> List[WeaponStatsItem]:
        player = self.player_repo.get_by_id(player_id)
        if player is None:
            raise PlayerNotFoundError(f"Player with id={player_id} not found")

        rows = self.stats_repo.get_player_stats_by_weapon(
            player_id=player_id,
            date_from=filters.date_from,
            date_to=filters.date_to,
            map_ids=filters.map_ids,
            mode_ids=filters.mode_ids,
            ranked_only=filters.ranked_only,
        )
        return [WeaponStatsItem(**row) for row in rows]

    # --- Глобальная статистика ---

    def get_global_map_stats(self, filters: GlobalStatsFilter) -> List[MapStatsItem]:
        rows = self.stats_repo.get_global_map_stats(
            date_from=filters.date_from,
            date_to=filters.date_to,
            ranked_only=filters.ranked_only,
        )
        return [MapStatsItem(**row) for row in rows]

    def get_global_mode_stats(self, filters: GlobalStatsFilter) -> List[ModeStatsItem]:
        rows = self.stats_repo.get_global_mode_stats(
            date_from=filters.date_from,
            date_to=filters.date_to,
            ranked_only=filters.ranked_only,
        )
        return [ModeStatsItem(**row) for row in rows]
