# app/db/repositories/battle_repository.py
from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Battle, BattleTeam, PlayerBattleStats, Player
from .base_repository import BaseRepository


class BattleRepository(BaseRepository[Battle]):
    """Операции над боями и сущностями вокруг них (в контексте игры)."""

    def __init__(self, session: Session, game_id: int | None = None) -> None:
        super().__init__(session, model=Battle, game_id=game_id)

    # --- Бои ---

    def create_battle(
        self,
        started_at: datetime,
        game_id: int | None = None,
        map_id: int | None = None,
        mode_id: int | None = None,
        is_ranked: bool = False,
        external_match_id: str | None = None,
    ) -> Battle:
        gid = game_id if game_id is not None else self.require_game_id()

        battle = Battle(
            game_id=gid,
            started_at=started_at,
            map_id=map_id,
            mode_id=mode_id,
            is_ranked=is_ranked,
            external_match_id=external_match_id,
        )
        self.session.add(battle)
        return battle

    def finish_battle(self, battle: Battle, ended_at: datetime | None = None) -> None:
        battle.ended_at = ended_at or datetime.utcnow()

    def get_by_id(self, battle_id: int, game_id: int | None = None) -> Optional[Battle]:
        gid = game_id if game_id is not None else self.require_game_id()
        stmt = select(Battle).where(Battle.id == battle_id, Battle.game_id == gid)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_battles(
        self,
        game_id: int | None = None,
        player_id: Optional[int] = None,
        map_id: Optional[int] = None,
        mode_id: Optional[int] = None,
        is_ranked: Optional[bool] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[Battle]:
        """
        Список боёв с фильтрами. Всегда ограничивается рамками game_id.
        """
        gid = game_id if game_id is not None else self.require_game_id()

        stmt = select(Battle).where(Battle.game_id == gid)

        if player_id is not None:
            stmt = (
                stmt.join(PlayerBattleStats, PlayerBattleStats.battle_id == Battle.id)
                .where(
                    PlayerBattleStats.player_id == player_id,
                    PlayerBattleStats.game_id == gid,
                )
            )

        if map_id is not None:
            stmt = stmt.where(Battle.map_id == map_id)

        if mode_id is not None:
            stmt = stmt.where(Battle.mode_id == mode_id)

        if is_ranked is not None:
            stmt = stmt.where(Battle.is_ranked == is_ranked)

        if date_from is not None:
            stmt = stmt.where(Battle.started_at >= date_from)

        if date_to is not None:
            stmt = stmt.where(Battle.started_at <= date_to)

        stmt = stmt.order_by(Battle.started_at.desc()).offset(offset).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def list_battles_for_player(
        self,
        player_id: int,
        game_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Battle]:
        gid = game_id if game_id is not None else self.require_game_id()

        stmt = (
            select(Battle)
            .join(PlayerBattleStats, PlayerBattleStats.battle_id == Battle.id)
            .where(
                Battle.game_id == gid,
                PlayerBattleStats.game_id == gid,
                PlayerBattleStats.player_id == player_id,
            )
            .order_by(Battle.started_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    # --- Команды ---

    def add_teams(
        self,
        battle: Battle,
        teams: Iterable[tuple[int, str | None]],
    ) -> List[BattleTeam]:
        result: List[BattleTeam] = []
        for team_index, name in teams:
            team = BattleTeam(
                battle=battle,
                team_index=team_index,
                name=name,
            )
            self.session.add(team)
            result.append(team)
        return result

    # --- Участие игрока в бою ---

    def add_player_to_battle(
        self,
        battle: Battle,
        player: Player,
        team: BattleTeam | None = None,
    ) -> PlayerBattleStats:
        # Жёсткая изоляция: игрок и бой должны быть одной игры
        if player.game_id != battle.game_id:
            raise ValueError("Player and Battle belong to different games")

        stats = PlayerBattleStats(
            game_id=battle.game_id,
            battle=battle,
            player=player,
            team=team,
            kills=0,
            deaths=0,
            assists=0,
            damage_dealt=0,
            damage_taken=0,
            score=0,
            headshots=0,
        )
        self.session.add(stats)
        return stats

    def get_player_stats_in_battle(
        self,
        battle_id: int,
        player_id: int,
        game_id: int | None = None,
    ) -> Optional[PlayerBattleStats]:
        gid = game_id if game_id is not None else self.require_game_id()

        stmt = (
            select(PlayerBattleStats)
            .where(
                PlayerBattleStats.game_id == gid,
                PlayerBattleStats.battle_id == battle_id,
                PlayerBattleStats.player_id == player_id,
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()
