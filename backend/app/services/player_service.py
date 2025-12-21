# app/services/player_service.py
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import PlayerNotFoundError, PlayerAlreadyExistsError
from app.db.repositories.player_repository import PlayerRepository
from app.db.repositories.stats_repository import StatsRepository
from app.schemas.player import (
    PlayerCreate,
    PlayerRead,
    PlayerListItem,
    PlayerStatsSummary,
    PlayerWithStatsSummary,
)
from app.schemas.stats import PlayerStatsFilter


class PlayerService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.player_repo = PlayerRepository(session)
        self.stats_repo = StatsRepository(session)

    # --- CRUD по игрокам ---

    def create_player(self, game_id: int, data: PlayerCreate) -> PlayerRead:
        # nickname уникален в рамках game_id
        existing = self.player_repo.with_game(game_id).get_by_nickname(data.nickname)
        if existing is not None:
            raise PlayerAlreadyExistsError(
                f"Player with nickname '{data.nickname}' already exists in game_id={game_id}"
            )

        player = self.player_repo.with_game(game_id).create(
            nickname=data.nickname,
            user_id=data.user_id,
        )
        self.session.commit()
        self.session.refresh(player)
        return PlayerRead.from_orm(player)

    def get_player(self, game_id: int, player_id: int) -> PlayerRead:
        player = self.player_repo.with_game(game_id).get_by_id(player_id)
        if player is None:
            raise PlayerNotFoundError(f"Player with id={player_id} not found in game_id={game_id}")
        return PlayerRead.from_orm(player)

    def list_players(self, game_id: int, offset: int = 0, limit: int = 100) -> list[PlayerListItem]:
        players = self.player_repo.with_game(game_id).list_players(offset=offset, limit=limit)
        return [PlayerListItem.from_orm(p) for p in players]

    def delete_player(self, game_id: int, player_id: int) -> None:
        player = self.player_repo.with_game(game_id).get_by_id(player_id)
        if player is None:
            raise PlayerNotFoundError(f"Player with id={player_id} not found in game_id={game_id}")
        self.player_repo.delete(player)
        self.session.commit()

    # --- Статистика игрока ---

    def get_player_stats_summary(self, game_id: int, player_id: int, filters: PlayerStatsFilter) -> PlayerWithStatsSummary:
        player = self.player_repo.with_game(game_id).get_by_id(player_id)
        if player is None:
            raise PlayerNotFoundError(f"Player with id={player_id} not found in game_id={game_id}")

        raw = self.stats_repo.with_game(game_id).get_player_stats_summary(player_id=player_id)

        # raw может быть None, если боёв нет
        if raw is None:
            stats = PlayerStatsSummary(
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
        else:
            stats = PlayerStatsSummary(**raw)

        return PlayerWithStatsSummary(
            player=PlayerRead.from_orm(player),
            stats=stats,
        )
