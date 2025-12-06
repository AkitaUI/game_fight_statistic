# app/services/battle_service.py
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import (
    BattleNotFoundError,
    BattleAlreadyFinishedError,
    InvalidBattleOperationError,
    PlayerNotFoundError,
)
from app.db.repositories.battle_repository import BattleRepository
from app.db.repositories.player_repository import PlayerRepository
from app.schemas.battle import (
    BattleCreate,
    BattleRead,
    BattleListItem,
    BattleTeamCreate,
    BattleTeamRead,
    PlayerBattleStatsCreate,
    PlayerBattleStatsRead,
)
from app.schemas.battle import WeaponStatsItem as WeaponStatsInBattleDTO


class BattleService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.battle_repo = BattleRepository(session)
        self.player_repo = PlayerRepository(session)

    # --- Вспомогательные методы ---

    def _ensure_battle_exists(self, battle_id: int):
        battle = self.battle_repo.get_by_id(battle_id)
        if battle is None:
            raise BattleNotFoundError(f"Battle with id={battle_id} not found")
        return battle

    def _ensure_battle_not_finished(self, battle) -> None:
        if battle.ended_at is not None:
            raise BattleAlreadyFinishedError(f"Battle id={battle.id} already finished")

    # --- Операции над боем ---

    def create_battle(self, data: BattleCreate) -> BattleRead:
        # Проверки map_id/mode_id можно сделать через репозитории справочников
        battle = self.battle_repo.create_battle(
            map_id=data.map_id,
            mode_id=data.mode_id,
            is_ranked=data.is_ranked,
            started_at=data.started_at or datetime.utcnow(),
            external_match_id=data.external_match_id,
        )
        self.session.commit()
        self.session.refresh(battle)
        return BattleRead.from_orm(battle)

    def get_battle_details(self, battle_id: int) -> BattleRead:
        battle = self.battle_repo.get_with_details(battle_id)  # предполагаемый метод
        if battle is None:
            raise BattleNotFoundError(f"Battle with id={battle_id} not found")
        return BattleRead.from_orm(battle)

    def list_battles(
        self,
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

    # --- Команды ---

    def add_team_to_battle(self, battle_id: int, data: BattleTeamCreate) -> BattleTeamRead:
        battle = self._ensure_battle_exists(battle_id)
        self._ensure_battle_not_finished(battle)

        # Проверка уникальности team_index делается в репозитории (или здесь перед insert)
        team = self.battle_repo.add_team(
            battle_id=battle_id,
            team_index=data.team_index,
            name=data.name,
            is_winner=data.is_winner,
        )
        self.session.commit()
        self.session.refresh(team)
        return BattleTeamRead.from_orm(team)

    # --- Участие игрока в бою и статистика ---

    def add_player_stats(
        self,
        battle_id: int,
        data: PlayerBattleStatsCreate,
    ) -> PlayerBattleStatsRead:
        battle = self._ensure_battle_exists(battle_id)
        self._ensure_battle_not_finished(battle)

        player = self.player_repo.get_by_id(data.player_id)
        if player is None:
            raise PlayerNotFoundError(f"Player with id={data.player_id} not found")

        team = self.battle_repo.get_team_by_id(data.team_id)
        if team is None or team.battle_id != battle_id:
            raise InvalidBattleOperationError("Team does not belong to this battle")

        stats = self.battle_repo.add_player_stats(
            battle_id=battle_id,
            player_id=data.player_id,
            team_id=data.team_id,
            kills=data.kills,
            deaths=data.deaths,
            assists=data.assists,
            damage_dealt=data.damage_dealt,
            damage_taken=data.damage_taken,
            score=data.score,
            headshots=data.headshots,
            result=data.result,
            joined_at=data.joined_at,
            left_at=data.left_at,
        )

        # Оружие
        if data.weapon_stats:
            for ws in data.weapon_stats:
                self.battle_repo.add_weapon_stats(
                    player_battle_stats_id=stats.id,
                    weapon_id=ws.weapon_id,
                    shots_fired=ws.shots_fired,
                    hits=ws.hits,
                    kills=ws.kills,
                    headshots=ws.headshots,
                )

        self.session.commit()
        self.session.refresh(stats)

        # Нужно подгрузить weapon_stats, если не lazy
        stats = self.battle_repo.get_player_stats_with_weapons(stats.id)

        # Конвертация ORM → DTO
        weapon_dtos = [
            WeaponStatsInBattleDTO(
                weapon_id=w.weapon_id,
                shots_fired=w.shots_fired,
                hits=w.hits,
                kills=w.kills,
                headshots=w.headshots,
            )
            for w in stats.weapon_stats
        ]

        dto = PlayerBattleStatsRead.from_orm(stats)
        dto.weapon_stats = weapon_dtos
        return dto

    # --- Завершение боя ---

    def finish_battle(self, battle_id: int, ended_at: Optional[datetime] = None) -> BattleRead:
        battle = self._ensure_battle_exists(battle_id)
        self._ensure_battle_not_finished(battle)

        ended = ended_at or datetime.utcnow()
        battle = self.battle_repo.finish_battle(battle_id=battle_id, ended_at=ended)
        self.session.commit()
        self.session.refresh(battle)
        return BattleRead.from_orm(battle)
