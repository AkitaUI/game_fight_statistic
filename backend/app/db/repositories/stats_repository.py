# app/db/repositories/stats_repository.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from ..models import (
    Battle,
    Player,
    PlayerBattleStats,
    Weapon,
    WeaponStats,
)
from .base_repository import BaseRepository


class StatsRepository(BaseRepository[None]):
    """
    Репозиторий для агрегированной статистики.
    Здесь методы обычно возвращают dict/list, а не модели напрямую.
    """

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    # --- Общая статистика игрока ---

    def get_player_overview(self, player_id: int) -> Optional[Dict[str, Any]]:
        """
        Общий обзор статистики игрока:
        - общее число боёв
        - суммарные убийства/смерти/ассисты
        - K/D
        """
        stmt: Select = (
            select(
                func.count(PlayerBattleStats.id).label("matches"),
                func.coalesce(func.sum(PlayerBattleStats.kills), 0).label("kills"),
                func.coalesce(func.sum(PlayerBattleStats.deaths), 0).label("deaths"),
                func.coalesce(func.sum(PlayerBattleStats.assists), 0).label("assists"),
            )
            .where(PlayerBattleStats.player_id == player_id)
        )

        row = self.session.execute(stmt).mappings().one_or_none()
        if row is None:
            return None

        kills = row["kills"]
        deaths = row["deaths"]
        kd_ratio = float(kills) / deaths if deaths > 0 else float(kills)

        return {
            "matches": row["matches"],
            "kills": kills,
            "deaths": deaths,
            "assists": row["assists"],
            "kd_ratio": kd_ratio,
        }

    # --- Статистика по картам ---

    def get_player_stats_by_map(self, player_id: int) -> List[Dict[str, Any]]:
        """
        Статистика игрока по картам.
        """
        from ..models import Map  # локальный импорт, чтобы избежать циклов

        stmt: Select = (
            select(
                Map.id.label("map_id"),
                Map.name.label("map_name"),
                func.count(PlayerBattleStats.id).label("matches"),
                func.coalesce(func.sum(PlayerBattleStats.kills), 0).label("kills"),
                func.coalesce(func.sum(PlayerBattleStats.deaths), 0).label("deaths"),
            )
            .join(Battle, Battle.id == PlayerBattleStats.battle_id)
            .join(Map, Map.id == Battle.map_id)
            .where(PlayerBattleStats.player_id == player_id)
            .group_by(Map.id, Map.name)
            .order_by(func.count(PlayerBattleStats.id).desc())
        )

        rows = self.session.execute(stmt).mappings().all()
        result: List[Dict[str, Any]] = []
        for row in rows:
            kills = row["kills"]
            deaths = row["deaths"]
            kd_ratio = float(kills) / deaths if deaths > 0 else float(kills)
            result.append(
                {
                    "map_id": row["map_id"],
                    "map_name": row["map_name"],
                    "matches": row["matches"],
                    "kills": kills,
                    "deaths": deaths,
                    "kd_ratio": kd_ratio,
                }
            )
        return result

    # --- Статистика по оружию ---

    def get_player_weapon_stats(self, player_id: int) -> List[Dict[str, Any]]:
        """
        Статистика игрока по оружию.
        """
        stmt: Select = (
            select(
                Weapon.id.label("weapon_id"),
                Weapon.name.label("weapon_name"),
                func.coalesce(func.sum(WeaponStats.shots_fired), 0).label("shots_fired"),
                func.coalesce(func.sum(WeaponStats.hits), 0).label("hits"),
                func.coalesce(func.sum(WeaponStats.kills), 0).label("kills"),
                func.coalesce(func.sum(WeaponStats.headshots), 0).label("headshots"),
            )
            .join(
                PlayerBattleStats,
                PlayerBattleStats.id == WeaponStats.player_battle_stats_id,
            )
            .join(Weapon, Weapon.id == WeaponStats.weapon_id)
            .where(PlayerBattleStats.player_id == player_id)
            .group_by(Weapon.id, Weapon.name)
            .order_by(func.sum(WeaponStats.kills).desc())
        )

        rows = self.session.execute(stmt).mappings().all()
        result: List[Dict[str, Any]] = []
        for row in rows:
            shots = row["shots_fired"]
            hits = row["hits"]
            accuracy = float(hits) / shots if shots > 0 else 0.0
            result.append(
                {
                    "weapon_id": row["weapon_id"],
                    "weapon_name": row["weapon_name"],
                    "shots_fired": shots,
                    "hits": hits,
                    "kills": row["kills"],
                    "headshots": row["headshots"],
                    "accuracy": accuracy,
                }
            )
        return result

    # ------------------------------------------------------------------
    # ОБЁРТКИ ПОД ИМЕНА, КОТОРЫЕ ЖДУТ service/api
    # ------------------------------------------------------------------

    def get_player_stats_summary(
        self,
        player_id: int,
        filters: object | None = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Обёртка, которую вызывает StatsService.
        Сейчас просто игнорируем filters и используем get_player_overview.
        """
        return self.get_player_overview(player_id)

    def get_player_stats_by_maps(
        self,
        player_id: int,
        filters: object | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Обёртка над get_player_stats_by_map.
        filters пока игнорируем.
        """
        return self.get_player_stats_by_map(player_id)

    def get_player_stats_by_weapons(
        self,
        player_id: int,
        filters: object | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Обёртка над get_player_weapon_stats.
        filters пока игнорируем.
        """
        return self.get_player_weapon_stats(player_id)
