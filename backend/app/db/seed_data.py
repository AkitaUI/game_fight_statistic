# app/db/seed_data.py
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import text

from app.db.session import SessionLocal


def seed_sample_data() -> None:
    """
    Заполняет БД демонстрационными данными.

    NEW (важно для отзыва):
      - создаём 2 игры
      - все справочники и игроки привязаны к конкретной игре (game_id)
      - бои и статистика также привязаны к game_id
    """

    session = SessionLocal()
    try:
        # Если уже есть игры — считаем, что сидирование делали
        count_games = session.execute(text("SELECT COUNT(*) FROM games")).scalar_one()
        if count_games and count_games > 0:
            print("⚠ Sample data seems to be already present (games exist), skipping seeding.")
            return

        print("▶ Seeding sample data (multi-game)...")
        now = datetime.utcnow()

        # ------------------------------------------------------------------ #
        # 1) Игры
        # ------------------------------------------------------------------ #
        game1_id = session.execute(
            text(
                """
                INSERT INTO games (slug, name)
                VALUES (:slug, :name)
                RETURNING id
                """
            ),
            {"slug": "arena", "name": "Arena Fighters"},
        ).scalar_one()

        game2_id = session.execute(
            text(
                """
                INSERT INTO games (slug, name)
                VALUES (:slug, :name)
                RETURNING id
                """
            ),
            {"slug": "space", "name": "Space Skirmish"},
        ).scalar_one()

        # ------------------------------------------------------------------ #
        # 2) Справочники по каждой игре (maps, modes, weapons)
        # ------------------------------------------------------------------ #
        maps: dict[tuple[int, str], int] = {}
        modes: dict[tuple[int, str], int] = {}
        weapons: dict[tuple[int, str], int] = {}

        # Карты
        for gid, items in [
            (game1_id, [("Dust Arena", "Small symmetric desert-themed arena"), ("Frozen City", "Urban map covered with snow")]),
            (game2_id, [("Orbital Station", "Zero-gravity corridors"), ("Red Planet Base", "Martian outpost combat zone")]),
        ]:
            for name, desc in items:
                map_id = session.execute(
                    text(
                        """
                        INSERT INTO maps (game_id, name, description)
                        VALUES (:game_id, :name, :description)
                        RETURNING id
                        """
                    ),
                    {"game_id": gid, "name": name, "description": desc},
                ).scalar_one()
                maps[(gid, name)] = map_id

        # Режимы
        for gid, items in [
            (game1_id, [("TDM", "Team Deathmatch", "Two teams, most kills win"), ("DOM", "Domination", "Capture and hold control points")]),
            (game2_id, [("CTF", "Capture The Flag", "Steal enemy flag and return"), ("BR", "Battle Royale", "Last player/team standing")]),
        ]:
            for code, name, desc in items:
                mode_id = session.execute(
                    text(
                        """
                        INSERT INTO game_modes (game_id, code, name, description)
                        VALUES (:game_id, :code, :name, :description)
                        RETURNING id
                        """
                    ),
                    {"game_id": gid, "code": code, "name": name, "description": desc},
                ).scalar_one()
                modes[(gid, code)] = mode_id

        # Оружие
        for gid, items in [
            (game1_id, [("AK-97", "Rifle"), ("Desert Hawk", "Pistol"), ("Thunderbolt", "Sniper")]),
            (game2_id, [("Plasma Carbine", "Energy Rifle"), ("Ion Pistol", "Energy Pistol"), ("Railgun", "Sniper")]),
        ]:
            for name, category in items:
                weapon_id = session.execute(
                    text(
                        """
                        INSERT INTO weapons (game_id, name, category)
                        VALUES (:game_id, :name, :category)
                        RETURNING id
                        """
                    ),
                    {"game_id": gid, "name": name, "category": category},
                ).scalar_one()
                weapons[(gid, name)] = weapon_id

        # ------------------------------------------------------------------ #
        # 3) Игроки (по игре)
        # ------------------------------------------------------------------ #
        players: dict[tuple[int, str], int] = {}

        for gid, nicks in [
            (game1_id, ["AlphaWolf", "BravoFox", "CharlieEagle"]),
            (game2_id, ["NovaPilot", "CosmoRider", "StarHunter"]),
        ]:
            for nickname in nicks:
                player_id = session.execute(
                    text(
                        """
                        INSERT INTO players (game_id, user_id, nickname, created_at)
                        VALUES (:game_id, NULL, :nickname, :created_at)
                        RETURNING id
                        """
                    ),
                    {"game_id": gid, "nickname": nickname, "created_at": now},
                ).scalar_one()
                players[(gid, nickname)] = player_id

        # ------------------------------------------------------------------ #
        # 4) Бои (по игре)
        # ------------------------------------------------------------------ #
        battles: list[tuple[int, int]] = []  # (game_id, battle_id)

        battle_specs = [
            # game_id, map_name, mode_code, is_ranked, days_ago
            (game1_id, "Dust Arena", "TDM", True, 1),
            (game1_id, "Frozen City", "DOM", False, 2),
            (game2_id, "Orbital Station", "CTF", True, 1),
            (game2_id, "Red Planet Base", "BR", False, 3),
        ]

        for gid, map_name, mode_code, is_ranked, days_ago in battle_specs:
            started_at = now - timedelta(days=days_ago, hours=1)
            ended_at = started_at + timedelta(minutes=10)
            battle_id = session.execute(
                text(
                    """
                    INSERT INTO battles (
                        game_id,
                        started_at, ended_at,
                        map_id, mode_id,
                        created_at,
                        external_match_id,
                        is_ranked
                    )
                    VALUES (
                        :game_id,
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
                    "game_id": gid,
                    "started_at": started_at,
                    "ended_at": ended_at,
                    "map_id": maps[(gid, map_name)],
                    "mode_id": modes[(gid, mode_code)],
                    "created_at": started_at,
                    "external_match_id": f"{gid}-match-{days_ago}",
                    "is_ranked": is_ranked,
                },
            ).scalar_one()
            battles.append((gid, battle_id))

        # ------------------------------------------------------------------ #
        # 5) Команды в боях
        # ------------------------------------------------------------------ #
        teams_per_battle: dict[int, dict[str, int]] = {}

        for gid, battle_id in battles:
            teams_per_battle[battle_id] = {}
            for team_index, (name, is_winner) in enumerate([("Blue", True), ("Red", False)], start=1):
                team_id = session.execute(
                    text(
                        """
                        INSERT INTO battle_teams (battle_id, team_index, name, is_winner)
                        VALUES (:battle_id, :team_index, :name, :is_winner)
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
        # 6) Статистика игроков в боях (и game_id тоже!)
        # ------------------------------------------------------------------ #
        player_battle_stats_ids: list[tuple[int, int]] = []  # (game_id, pbs_id)

        # Пример: для каждого боя 2 игрока этой же игры
        for (gid, battle_id) in battles:
            # берём 2 любых игрока этой игры
            nick1 = next(n for (g, n) in players.keys() if g == gid)
            nick2 = [n for (g, n) in players.keys() if g == gid and n != nick1][0]

            participants = [
                (nick1, "Blue", 20, 10, 5, 2500),
                (nick2, "Red", 15, 15, 3, 1900),
            ]

            for nickname, team_name, kills, deaths, assists, score in participants:
                team_id = teams_per_battle[battle_id][team_name]
                player_id = players[(gid, nickname)]

                joined_at = now - timedelta(days=1)
                left_at = joined_at + timedelta(minutes=10)

                stats_id = session.execute(
                    text(
                        """
                        INSERT INTO player_battle_stats (
                            game_id,
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
                            :game_id,
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
                        "game_id": gid,
                        "battle_id": battle_id,
                        "player_id": player_id,
                        "team_id": team_id,
                        "kills": kills,
                        "deaths": deaths,
                        "assists": assists,
                        "damage_dealt": kills * 100,
                        "damage_taken": deaths * 80,
                        "score": score,
                        "headshots": max(0, kills // 3),
                        "result": 1 if team_name == "Blue" else -1,
                        "joined_at": joined_at,
                        "left_at": left_at,
                    },
                ).scalar_one()

                player_battle_stats_ids.append((gid, stats_id))

        # ------------------------------------------------------------------ #
        # 7) Статистика по оружию (только оружие той же игры!)
        # ------------------------------------------------------------------ #
        for gid, stats_id in player_battle_stats_ids:
            # выберем первое оружие данной игры
            weapon_name = next(name for (g, name) in weapons.keys() if g == gid)
            weapon_id = weapons[(gid, weapon_name)]

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
        print("✅ Sample data inserted successfully (multi-game).")

    except Exception as exc:  # noqa: BLE001
        session.rollback()
        print(f"❌ Error while seeding data: {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_sample_data()
