# app/services/stats_service.py
from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.core.exceptions import PlayerNotFoundError
from app.db.repositories.player_repository import PlayerRepository
from app.db.repositories.stats_repository import StatsRepository
from app.schemas.player import PlayerStatsSummary
from app.schemas.stats import PlayerStatsFilter, MapStatsItem, WeaponStatsItem


class StatsService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.player_repo = PlayerRepository(session)
        self.stats_repo = StatsRepository(session)

    # --- Статистика по игроку ---

    def get_player_summary(self, game_id: int, player_id: int, filters: PlayerStatsFilter) -> PlayerStatsSummary:
        player = self.player_repo.with_game(game_id).get_by_id(player_id)
        if player is None:
            raise PlayerNotFoundError(f"Player with id={player_id} not found in game_id={game_id}")

        raw = self.stats_repo.with_game(game_id).get_player_stats_summary(player_id=player_id)
        if raw is None:
            return PlayerStatsSummary(
                player_id=player_id,
                total_battles=0,
                wins=0,
                losses=0,
                draws=0,
                win_rate=0.0,
                total_kills=0,
                total_deaths=0,
                total_assists=0,
                avg_kd_ratio=0.0,
                total_damage_dealt=0,
                total_damage_taken=0,
                avg_score=0.0,
            )
        return PlayerStatsSummary(**raw)

    def get_player_map_stats(self, game_id: int, player_id: int, filters: PlayerStatsFilter) -> List[MapStatsItem]:
        player = self.player_repo.with_game(game_id).get_by_id(player_id)
        if player is None:
            raise PlayerNotFoundError(f"Player with id={player_id} not found in game_id={game_id}")

        rows = self.stats_repo.with_game(game_id).get_player_stats_by_map(player_id=player_id)
        return [MapStatsItem(**row) for row in rows]

    def get_player_weapon_stats(self, game_id: int, player_id: int, filters: PlayerStatsFilter) -> List[WeaponStatsItem]:
        player = self.player_repo.with_game(game_id).get_by_id(player_id)
        if player is None:
            raise PlayerNotFoundError(f"Player with id={player_id} not found in game_id={game_id}")

        rows = self.stats_repo.with_game(game_id).get_player_weapon_stats(player_id=player_id)
        return [WeaponStatsItem(**row) for row in rows]
