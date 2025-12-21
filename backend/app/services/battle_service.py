# app/services/battle_service.py
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import (
    BattleNotFoundError,
    BattleAlreadyFinishedError,
    PlayerNotFoundError,
    InvalidBattleOperationError,
)
from app.db.repositories.battle_repository import BattleRepository
from app.db.repositories.player_repository import PlayerRepository
from app.schemas.battle import BattleCreate, BattleRead, BattleListItem


class BattleService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.battle_repo = BattleRepository(session)
        self.player_repo = PlayerRepository(session)

    def _ensure_battle_exists(self, game_id: int, battle_id: int):
        battle = self.battle_repo.get_by_id(battle_id=battle_id, game_id=game_id)
        if battle is None:
            raise BattleNotFoundError(f"Battle with id={battle_id} not found in game_id={game_id}")
        return battle

    @staticmethod
    def _ensure_battle_not_finished(battle) -> None:
        if battle.ended_at is not None:
            raise BattleAlreadyFinishedError(f"Battle id={battle.id} already finished")

    # --- battle ops ---

    def create_battle(self, game_id: int, data: BattleCreate) -> BattleRead:
        battle = self.battle_repo.create_battle(
            game_id=game_id,
            map_id=data.map_id,
            mode_id=data.mode_id,
            is_ranked=data.is_ranked,
            started_at=data.started_at or datetime.utcnow(),
            external_match_id=data.external_match_id,
        )
        self.session.commit()
        self.session.refresh(battle)
        return BattleRead.from_orm(battle)

    def get_battle_details(self, game_id: int, battle_id: int) -> BattleRead:
        battle = self._ensure_battle_exists(game_id, battle_id)
        return BattleRead.from_orm(battle)

    def list_battles(
        self,
        game_id: int,
        player_id: Optional[int] = None,
        map_id: Optional[int] = None,
        mode_id: Optional[int] = None,
        is_ranked: Optional[bool] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[BattleListItem]:
        battles = self.battle_repo.list_battles(
            game_id=game_id,
            player_id=player_id,
            map_id=map_id,
            mode_id=mode_id,
            is_ranked=is_ranked,
            date_from=date_from,
            date_to=date_to,
            offset=offset,
            limit=limit,
        )
        return [BattleListItem.from_orm(b) for b in battles]

    # --- participation (минимально) ---

    def add_player_to_battle(self, game_id: int, battle_id: int, player_id: int) -> None:
        battle = self._ensure_battle_exists(game_id, battle_id)
        self._ensure_battle_not_finished(battle)

        player = self.player_repo.get_by_id(player_id=player_id, game_id=game_id)
        if player is None:
            raise PlayerNotFoundError(f"Player with id={player_id} not found in game_id={game_id}")

        try:
            self.battle_repo.add_player_to_battle(battle=battle, player=player, team=None)
        except ValueError as exc:
            raise InvalidBattleOperationError(str(exc)) from exc

        self.session.commit()

    # --- finish ---

    def finish_battle(self, game_id: int, battle_id: int, ended_at: Optional[datetime] = None) -> BattleRead:
        battle = self._ensure_battle_exists(game_id, battle_id)
        self._ensure_battle_not_finished(battle)

        self.battle_repo.finish_battle(battle, ended_at=ended_at)
        self.session.commit()
        self.session.refresh(battle)
        return BattleRead.from_orm(battle)
