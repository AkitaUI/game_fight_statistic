# app/db/repositories/player_repository.py
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Player
from .base_repository import BaseRepository


class PlayerRepository(BaseRepository[Player]):
    """Операции над сущностью Player (в контексте конкретной игры)."""

    def __init__(self, session: Session, game_id: int | None = None) -> None:
        super().__init__(session, model=Player, game_id=game_id)

    def get_by_id(self, player_id: int, game_id: int | None = None) -> Optional[Player]:
        gid = game_id if game_id is not None else self.require_game_id()
        stmt = select(Player).where(Player.id == player_id, Player.game_id == gid)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_nickname(self, nickname: str, game_id: int | None = None) -> Optional[Player]:
        gid = game_id if game_id is not None else self.require_game_id()
        stmt = select(Player).where(Player.game_id == gid, Player.nickname == nickname)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_players(
        self,
        game_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Player]:
        gid = game_id if game_id is not None else self.require_game_id()
        stmt = (
            select(Player)
            .where(Player.game_id == gid)
            .order_by(Player.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def create(self, nickname: str, user_id: int | None = None, game_id: int | None = None) -> Player:
        gid = game_id if game_id is not None else self.require_game_id()
        player = Player(
            game_id=gid,
            nickname=nickname,
            user_id=user_id,
        )
        self.session.add(player)
        return player

    def delete(self, player: Player) -> None:
        self.session.delete(player)
