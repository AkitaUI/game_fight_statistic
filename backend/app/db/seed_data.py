# app/db/seed_data.py
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import text

from app.db.session import SessionLocal


def seed_sample_data() -> None:
    """
    Заполняет БД демонстрационными данными для карт, режимов, оружия,
    игроков и нескольких боёв со статистикой.

    Предполагается, что:
      - миграции уже применены (все таблицы существуют);
      - запускается на "пустой" БД (или хотя бы без игроков).
    """

    session = SessionLocal()
    try:
        # Проверяем, есть ли уже игроки — если да, считаем что данные уже есть
        count_players = session.execute(
            text("SELECT COUNT(*) FROM players")
        ).scalar_one()

        if count_players and count_players > 0:
            print("⚠ Sample data seems to be already present, skipping seeding.")
            return

        print("▶ Seeding sample data...")

        # ------------------------------------------------------------------ #
        # 1. Справочники: карты, режимы, оружие
        # ------------------------------------------------------------------ #
        maps: dict[str, int] = {}
        game_modes: dict[str, int] = {}
        weapons: dict[str, int] = {}

        # Карты
        for name, desc in [
            ("Dust Arena", "Small symmetric desert-themed arena"),
            ("Frozen City", "Urban map covered with snow"),
        ]:
            map_id = session.execute(
                text(
                    """
                    INSERT INTO maps (name, description)
                    VALUES (:name, :description)
                    RETURNING id
                    """
                ),
                {"name": name, "description": desc},
            ).scalar_one()
            maps[name] = map_id

        # Режимы
        for code, name, desc in [
            ("TDM", "Team Deathmatch", "Two teams, most kills win"),
            ("DOM", "Domination", "Capture and hold control points"),
        ]:
            mode_id = session.execute(
                text(
                    """
                    INSERT INTO game_modes (code, name, description)
                    VALUES (:code, :name, :description)
                    RETURNING id
                    """
                ),
                {"code": code, "name": name, "description": desc},
            ).scalar_one()
            game_modes[code] = mode_id

        # Оружие
        for name, category in [
            ("AK-97", "Rifle"),
            ("Desert Hawk", "Pistol"),
            ("Thunderbolt", "Sniper"),
        ]:
            weapon_id = session.execute(
                text(
                    """
                    INSERT INTO weapons (name, category)
                    VALUES (:name, :category)
                    RETURNING id
                    """
                ),
                {"name": name, "category": category},
            ).scalar_one()
            weapons[name] = weapon_id

        # ------------------------------------------------------------------ #
        # 2. Игроки
        # ------------------------------------------------------------------ #
        players: dict[str, int] = {}
        now = datetime.utcnow()

        for nickname in ["AlphaWolf", "BravoFox", "CharlieEagle"]:
            player_id = session.execute(
                text(
                    """
                    INSERT INTO players (user_id, nickname, created_at)
                    VALUES (NULL, :nickname, :created_at)
                    RETURNING id
                    """
                ),
                {"nickname": nickname, "created_at": now},
            ).scalar_one()
            players[nickname] = player_id

        # ------------------------------------------------------------------ #
        # 3. Пара тестовых боёв
        # ------------------------------------------------------------------ #
        battles: list[int] = []

        battle_specs = [
            # (map_name, mode_code, is_ranked, days_ago)
            ("Dust Arena", "TDM", True, 1),
            ("Frozen City", "DOM", False, 2),
        ]

        for map_name, mode_code, is_ranked, days_ago in battle_specs:
            started_at = now - timedelta(days=days_ago, hours=1)
            ended_at = started_at + timedelta(minutes=10)
            battle_id = session.execute(
                text(
                    """
                    INSERT INTO battles (
                        started_at, ended_at,
                        map_id, mode_id,
                        created_at,
                        external_match_id,
                        is_ranked
                    )
                    VALUES (
                        :started_at, :ended_at,
                        :map_id, :mode_id,
                        :created_at,
                        :external_match_id,
                        :is_ranked
                    )
                    RETURNING id
                    """
                ),
                {
                    "started_at": started_at,
                    "ended_at": ended_at,
                    "map_id": maps[map_name],
                    "mode_id": game_modes[mode_code],
                    "created_at": started_at,
                    "external_match_id": f"match-{days_ago}",
                    "is_ranked": is_ranked,
                },
            ).scalar_one()
            battles.append(battle_id)

        # ------------------------------------------------------------------ #
        # 4. Команды в боях (по две на бой)
        # ------------------------------------------------------------------ #
        teams_per_battle: dict[int, dict[str, int]] = {}

        for idx, battle_id in enumerate(battles, start=1):
            teams_per_battle[battle_id] = {}
            for team_index, (name, is_winner) in enumerate(
                [("Blue", True), ("Red", False)], start=1
            ):
                team_id = session.execute(
                    text(
                        """
                        INSERT INTO battle_teams (
                            battle_id, team_index, name, is_winner
                        )
                        VALUES (
                            :battle_id, :team_index, :name, :is_winner
                        )
                        RETURNING id
                        """
                    ),
                    {
                        "battle_id": battle_id,
                        "team_index": team_index,
                        "name": name,
                        "is_winner": is_winner,
                    },
                ).scalar_one()
                teams_per_battle[battle_id][name] = team_id

        # ------------------------------------------------------------------ #
        # 5. Статистика игроков в боях
        # ------------------------------------------------------------------ #
        # Для простоты: в каждом бою участвуют два игрока
        player_battle_stats_ids: list[int] = []

        battle_players = [
            # battle_idx -> (player, team_name, kills, deaths, assists, score)
            (0, "AlphaWolf", "Blue", 20, 10, 5, 2500),
            (0, "BravoFox", "Red",  15, 15, 3, 1900),
            (1, "AlphaWolf", "Red", 10, 12, 4, 1600),
            (1, "CharlieEagle", "Blue", 18, 8, 6, 2700),
        ]

        for battle_idx, nickname, team_name, kills, deaths, assists, score in battle_players:
            battle_id = battles[battle_idx]
            team_id = teams_per_battle[battle_id][team_name]
            player_id = players[nickname]

            joined_at = now - timedelta(days=1)
            left_at = joined_at + timedelta(minutes=10)

            stats_id = session.execute(
                text(
                    """
                    INSERT INTO player_battle_stats (
                        battle_id,
                        player_id,
                        team_id,
                        kills,
                        deaths,
                        assists,
                        damage_dealt,
                        damage_taken,
                        score,
                        headshots,
                        result,
                        joined_at,
                        left_at
                    )
                    VALUES (
                        :battle_id,
                        :player_id,
                        :team_id,
                        :kills,
                        :deaths,
                        :assists,
                        :damage_dealt,
                        :damage_taken,
                        :score,
                        :headshots,
                        :result,
                        :joined_at,
                        :left_at
                    )
                    RETURNING id
                    """
                ),
                {
                    "battle_id": battle_id,
                    "player_id": player_id,
                    "team_id": team_id,
                    "kills": kills,
                    "deaths": deaths,
                    "assists": assists,
                    "damage_dealt": kills * 100,   # грубая прикидка
                    "damage_taken": deaths * 80,
                    "score": score,
                    "headshots": max(0, kills // 3),
                    "result": 1 if team_name == "Blue" else -1,
                    "joined_at": joined_at,
                    "left_at": left_at,
                },
            ).scalar_one()

            player_battle_stats_ids.append(stats_id)

        # ------------------------------------------------------------------ #
        # 6. Статистика по оружию
        # ------------------------------------------------------------------ #
        # Присвоим условно каждому участию по одному оружию
        for stats_id, weapon_name in zip(
            player_battle_stats_ids,
            ["AK-97", "Desert Hawk", "Thunderbolt", "AK-97"],
        ):
            weapon_id = weapons[weapon_name]
            session.execute(
                text(
                    """
                    INSERT INTO weapon_stats (
                        player_battle_stats_id,
                        weapon_id,
                        shots_fired,
                        hits,
                        kills,
                        headshots
                    )
                    VALUES (
                        :pbs_id,
                        :weapon_id,
                        :shots_fired,
                        :hits,
                        :kills,
                        :headshots
                    )
                    """
                ),
                {
                    "pbs_id": stats_id,
                    "weapon_id": weapon_id,
                    "shots_fired": 200,
                    "hits": 80,
                    "kills": 10,
                    "headshots": 3,
                },
            )

        session.commit()
        print("✅ Sample data inserted successfully.")

    except Exception as exc:  # noqa: BLE001
        session.rollback()
        print(f"❌ Error while seeding data: {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_sample_data()
