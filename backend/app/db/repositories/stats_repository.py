# app/db/repositories/stats_repository.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import Select, func, select, case
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

    def get_player_stats_by_map(
        self,
        player_id: int,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """
        Статистика игрока по картам.
        Возвращает формат, соответствующий MapStatsItem из StatsService.
        """

        from ..models import Map  # чтобы избежать циклических импортов

        stmt = (
            select(
                Map.id.label("map_id"),
                Map.name.label("map_name"),

                func.count(PlayerBattleStats.id).label("battles"),

                func.coalesce(
                    func.sum(
                        case((PlayerBattleStats.result == 1, 1), else_=0)
                    ),
                    0,
                ).label("wins"),

                func.coalesce(
                    func.sum(
                        case((PlayerBattleStats.result == -1, 1), else_=0)
                    ),
                    0,
                ).label("losses"),

                func.coalesce(
                    func.sum(
                        case((PlayerBattleStats.result == 0, 1), else_=0)
                    ),
                    0,
                ).label("draws"),

                func.coalesce(func.avg(PlayerBattleStats.kills), 0).label("avg_kills"),
                func.coalesce(func.avg(PlayerBattleStats.deaths), 0).label("avg_deaths"),
                func.coalesce(func.avg(PlayerBattleStats.score), 0).label("avg_score"),
            )
            .join(Battle, Battle.id == PlayerBattleStats.battle_id)
            .join(Map, Map.id == Battle.map_id)
            .where(PlayerBattleStats.player_id == player_id)
            .group_by(Map.id, Map.name)
            .order_by(Map.id)
        )

        rows = self.session.execute(stmt).mappings().all()

        result = []
        for row in rows:
            battles = row["battles"]
            wins = row["wins"]
            losses = row["losses"]

            if battles > 0:
                win_rate = wins / battles
            else:
                win_rate = 0.0

            result.append(
                {
                    "map_id": row["map_id"],
                    "map_name": row["map_name"],
                    "battles": battles,
                    "wins": wins,
                    "losses": losses,
                    "win_rate": win_rate,
                    "avg_kills": row["avg_kills"],
                    "avg_deaths": row["avg_deaths"],
                    "avg_score": row["avg_score"],
                }
            )

        return result


    # --- Статистика по оружию ---

    def get_player_weapon_stats(self, player_id: int) -> List[Dict[str, Any]]:
        """
        Статистика игрока по оружию.
        Добавляем также usage_count — сколько раз оружие встречалось
        в записях WeaponStats для этого игрока.
        """
        stmt: Select = (
            select(
                Weapon.id.label("weapon_id"),
                Weapon.name.label("weapon_name"),
                func.coalesce(func.sum(WeaponStats.shots_fired), 0).label("shots_fired"),
                func.coalesce(func.sum(WeaponStats.hits), 0).label("hits"),
                func.coalesce(func.sum(WeaponStats.kills), 0).label("kills"),
                func.coalesce(func.sum(WeaponStats.headshots), 0).label("headshots"),
                func.count().label("usage_count"),
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
                    "usage_count": row["usage_count"],
                }
            )
        return result

    # ------------------------------------------------------------------
    # ОБЁРТКИ ПОД ИМЕНА, КОТОРЫЕ ЖДУТ service/api
    # ------------------------------------------------------------------

    def get_player_stats_summary(
        self,
        player_id: int,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        """
        Сводная статистика игрока в формате, который ожидает PlayerStatsSummary.
        """
        stmt: Select = (
            select(
                PlayerBattleStats.player_id.label("player_id"),
                func.count(PlayerBattleStats.id).label("total_battles"),
                func.coalesce(
                    func.sum(
                        case(
                            (PlayerBattleStats.result == 1, 1),
                            else_=0,
                        )
                    ),
                    0,
                ).label("wins"),
                func.coalesce(
                    func.sum(
                        case(
                            (PlayerBattleStats.result == -1, 1),
                            else_=0,
                        )
                    ),
                    0,
                ).label("losses"),
                func.coalesce(
                    func.sum(
                        case(
                            (PlayerBattleStats.result == 0, 1),
                            else_=0,
                        )
                    ),
                    0,
                ).label("draws"),
                func.coalesce(
                    func.sum(PlayerBattleStats.kills),
                    0,
                ).label("total_kills"),
                func.coalesce(
                    func.sum(PlayerBattleStats.deaths),
                    0,
                ).label("total_deaths"),
                func.coalesce(
                    func.sum(PlayerBattleStats.assists),
                    0,
                ).label("total_assists"),
                func.coalesce(
                    func.sum(PlayerBattleStats.damage_dealt),
                    0,
                ).label("total_damage_dealt"),
                func.coalesce(
                    func.sum(PlayerBattleStats.damage_taken),
                    0,
                ).label("total_damage_taken"),
                func.coalesce(
                    func.avg(PlayerBattleStats.score),
                    0,
                ).label("avg_score"),
            )
            .where(PlayerBattleStats.player_id == player_id)
            .group_by(PlayerBattleStats.player_id)
        )

        row = self.session.execute(stmt).mappings().one_or_none()
        if row is None:
            return None

        total_battles = row["total_battles"]
        if total_battles == 0:
            return None

        total_kills = row["total_kills"]
        total_deaths = row["total_deaths"]
        wins = row["wins"]

        # Win rate и средний K/D
        win_rate = float(wins) / total_battles if total_battles > 0 else 0.0
        avg_kd_ratio = (
            float(total_kills) / total_deaths if total_deaths > 0 else float(total_kills)
        )

        return {
            "player_id": row["player_id"],
            "total_battles": total_battles,
            "wins": wins,
            "losses": row["losses"],
            "draws": row["draws"],
            "win_rate": win_rate,
            "total_kills": total_kills,
            "total_deaths": total_deaths,
            "total_assists": row["total_assists"],
            "avg_kd_ratio": avg_kd_ratio,
            "total_damage_dealt": row["total_damage_dealt"],
            "total_damage_taken": row["total_damage_taken"],
            "avg_score": row["avg_score"],
        }


    def get_player_stats_by_maps(
        self,
        player_id: int,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """
        Обёртка над get_player_stats_by_map.
        """
        return self.get_player_stats_by_map(player_id)

    def get_player_stats_by_weapons(
        self,
        player_id: int,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """
        Обёртка над get_player_weapon_stats.
        """
        return self.get_player_weapon_stats(player_id)

    def get_player_stats_by_weapon(
        self,
        player_id: int,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """
        Алиас под имя, которое ожидает StatsService:
        get_player_stats_by_weapon -> get_player_weapon_stats.
        """
        return self.get_player_weapon_stats(player_id)
