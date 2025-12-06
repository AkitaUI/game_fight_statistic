# app/db/repositories/player_repository.py

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Player
from .base_repository import BaseRepository


class PlayerRepository(BaseRepository[Player]):
    """Операции над сущностью Player."""

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def get_by_id(self, player_id: int) -> Optional[Player]:
        stmt = select(Player).where(Player.id == player_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_nickname(self, nickname: str) -> Optional[Player]:
        stmt = select(Player).where(Player.nickname == nickname)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_players(self, limit: int = 100, offset: int = 0) -> List[Player]:
        stmt = (
            select(Player)
            .order_by(Player.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def create(self, nickname: str, user_id: int | None = None) -> Player:
        player = Player(
            nickname=nickname,
            user_id=user_id,
        )
        self.session.add(player)
        # commit делается снаружи (через контекстный менеджер get_session)
        return player

    def delete(self, player: Player) -> None:
        self.session.delete(player)
