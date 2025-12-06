# app/services/player_service.py
from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.core.exceptions import (
    PlayerNotFoundError,
    PlayerAlreadyExistsError,
)
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

    def create_player(self, data: PlayerCreate) -> PlayerRead:
        existing = self.player_repo.get_by_nickname(data.nickname)
        if existing is not None:
            raise PlayerAlreadyExistsError(f"Player with nickname '{data.nickname}' already exists")

        player = self.player_repo.create_player(
            nickname=data.nickname,
            user_id=data.user_id,
        )
        self.session.commit()
        self.session.refresh(player)
        return PlayerRead.from_orm(player)

    def get_player(self, player_id: int) -> PlayerRead:
        player = self.player_repo.get_by_id(player_id)
        if player is None:
            raise PlayerNotFoundError(f"Player with id={player_id} not found")
        return PlayerRead.from_orm(player)

    def list_players(self, offset: int = 0, limit: int = 100) -> list[PlayerListItem]:
        players = self.player_repo.list_players(offset=offset, limit=limit)
        return [PlayerListItem.from_orm(p) for p in players]

    def delete_player(self, player_id: int) -> None:
        player = self.player_repo.get_by_id(player_id)
        if player is None:
            raise PlayerNotFoundError(f"Player with id={player_id} not found")
        self.player_repo.delete(player)
        self.session.commit()

    # --- Статистика игрока ---

    def get_player_stats_summary(
        self,
        player_id: int,
        filters: PlayerStatsFilter,
    ) -> PlayerWithStatsSummary:
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
        # Ожидаем, что stats_repository вернёт dict с ключами, совпадающими с PlayerStatsSummary
        stats = PlayerStatsSummary(**raw)

        return PlayerWithStatsSummary(
            player=PlayerRead.from_orm(player),
            stats=stats,
        )
