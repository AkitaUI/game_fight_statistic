# app/db/seed_data.py
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import text

from app.db.session import SessionLocal


def _has_column(session, table_name: str, column_name: str) -> bool:
    q = text(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = :table
          AND column_name = :column
        LIMIT 1
        """
    )
    return session.execute(q, {"table": table_name, "column": column_name}).scalar_one_or_none() is not None


def _get_or_create_game(session, slug: str, name: str) -> int:
    row = session.execute(
        text("SELECT id FROM games WHERE slug = :slug LIMIT 1"),
        {"slug": slug},
    ).mappings().one_or_none()

    if row is not None:
        return int(row["id"])

    return session.execute(
        text(
            """
            INSERT INTO games (slug, name)
            VALUES (:slug, :name)
            RETURNING id
            """
        ),
        {"slug": slug, "name": name},
    ).scalar_one()


def seed_sample_data() -> None:
    """
    Заполняет БД демонстрационными данными.

    Цель:
      - гарантированно заполнить справочники (maps, game_modes, weapons),
        чтобы Swagger/UI могли создавать battles без game_id=0 и map_id/mode_id=0.
      - поддержать multi-game, если в таблицах есть колонка game_id,
        и не падать, если game_id там нет (тогда справочники общие).
    """
    session = SessionLocal()
    try:
        now = datetime.utcnow()

        # --- Определяем, есть ли game_id в таблицах справочников/игроков ---
        maps_has_game = _has_column(session, "maps", "game_id")
        modes_has_game = _has_column(session, "game_modes", "game_id")
        weapons_has_game = _has_column(session, "weapons", "game_id")
        players_has_game = _has_column(session, "players", "game_id")

        # --- Скип: считаем, что сид уже сделан, если карты уже существуют ---
        maps_count = session.execute(text("SELECT COUNT(*) FROM maps")).scalar_one()
        if maps_count and maps_count > 0:
            print("⚠ Sample data seems to be already present (maps exist), skipping seeding.")
            return

        print("▶ Seeding sample data...")

        # --- 1) Игры (get-or-create) ---
        # ВАЖНО: у тебя уже есть default (id=1). Мы его не ломаем.
        default_game_id = _get_or_create_game(session, slug="default", name="Default Game")

        # Вторую игру создаём для multi-game демонстрации
        arena_game_id = _get_or_create_game(session, slug="arena", name="Arena Fighters")
        space_game_id = _get_or_create_game(session, slug="space", name="Space Skirmish")

        # Список игр для последующих вставок
        game_ids = [arena_game_id, space_game_id]

        # --- 2) Справочники (maps, modes, weapons) ---
        maps: dict[tuple[int, str], int] = {}
        modes: dict[tuple[int, str], int] = {}
        weapons: dict[tuple[int, str], int] = {}

        # 2.1 Карты
        per_game_maps = [
            (arena_game_id, [("Dust Arena", "Small symmetric desert-themed arena"),
                             ("Frozen City", "Urban map covered with snow")]),
            (space_game_id, [("Orbital Station", "Zero-gravity corridors"),
                             ("Red Planet Base", "Martian outpost combat zone")]),
        ]

        if maps_has_game:
            for gid, items in per_game_maps:
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
        else:
            # таблица maps без game_id -> общий справочник
            # вставим только 2 карты, но так, чтобы battles могли ссылаться на них
            for name, desc in [("Dust Arena", "Small symmetric desert-themed arena"),
                               ("Frozen City", "Urban map covered with snow")]:
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
                # будем считать, что оба game используют эти id
                for gid in game_ids:
                    maps[(gid, name)] = map_id

        # 2.2 Режимы
        per_game_modes = [
            (arena_game_id, [("TDM", "Team Deathmatch", "Two teams, most kills win"),
                             ("DOM", "Domination", "Capture and hold control points")]),
            (space_game_id, [("CTF", "Capture The Flag", "Steal enemy flag and return"),
                             ("BR", "Battle Royale", "Last player/team standing")]),
        ]

        if modes_has_game:
            for gid, items in per_game_modes:
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
        else:
            # общий справочник
            for code, name, desc in [("TDM", "Team Deathmatch", "Two teams, most kills win"),
                                     ("DOM", "Domination", "Capture and hold control points")]:
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
                for gid in game_ids:
                    modes[(gid, code)] = mode_id

        # 2.3 Оружие
        per_game_weapons = [
            (arena_game_id, [("AK-97", "Rifle"), ("Desert Hawk", "Pistol"), ("Thunderbolt", "Sniper")]),
            (space_game_id, [("Plasma Carbine", "Energy Rifle"), ("Ion Pistol", "Energy Pistol"), ("Railgun", "Sniper")]),
        ]

        if weapons_has_game:
            for gid, items in per_game_weapons:
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
        else:
            # общий справочник
            for name, category in [("AK-97", "Rifle"), ("Desert Hawk", "Pistol"), ("Thunderbolt", "Sniper")]:
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
                for gid in game_ids:
                    weapons[(gid, name)] = weapon_id

        # --- 3) Игроки ---
        players: dict[tuple[int, str], int] = {}

        per_game_players = [
            (arena_game_id, ["AlphaWolf", "BravoFox", "CharlieEagle"]),
            (space_game_id, ["NovaPilot", "CosmoRider", "StarHunter"]),
        ]

        if players_has_game:
            for gid, nicks in per_game_players:
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
        else:
            # players без game_id -> общий пул игроков
            for nickname in ["AlphaWolf", "BravoFox", "CharlieEagle", "NovaPilot", "CosmoRider", "StarHunter"]:
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
                # распределим по играм логически (для battles)
                # первые 3 — arena, вторые 3 — space
                if nickname in ["AlphaWolf", "BravoFox", "CharlieEagle"]:
                    players[(arena_game_id, nickname)] = player_id
                else:
                    players[(space_game_id, nickname)] = player_id

        # --- 4) Бои (ВНИМАНИЕ: battles всегда с game_id!) ---
        battles: list[tuple[int, int]] = []  # (game_id, battle_id)

        battle_specs = [
            (arena_game_id, "Dust Arena", "TDM", True, 1),
            (arena_game_id, "Frozen City", "DOM", False, 2),
            (space_game_id, "Orbital Station", "CTF", True, 1),
            (space_game_id, "Red Planet Base", "BR", False, 3),
        ]

        # Если справочники общие (без game_id), то у space нет CTF/BR и orbital/red planet.
        # В этом случае создадим только 2 боя в arena, чтобы сид не падал.
        if (not maps_has_game) or (not modes_has_game):
            battle_specs = [
                (arena_game_id, "Dust Arena", "TDM", True, 1),
                (arena_game_id, "Frozen City", "DOM", False, 2),
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

        # --- 5) Команды в боях ---
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

        # --- 6) Статистика игроков в боях (player_battle_stats с game_id) ---
        player_battle_stats_ids: list[tuple[int, int]] = []  # (game_id, pbs_id)

        for gid, battle_id in battles:
            # возьмём 2 игрока данной игры
            game_nicks = [n for (g, n) in players.keys() if g == gid]
            nick1 = game_nicks[0]
            nick2 = game_nicks[1]

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

        # --- 7) weapon_stats (оружие той же игры, если оно per-game; иначе — общий) ---
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
        print("✅ Sample data inserted successfully.")

    except Exception as exc:  # noqa: BLE001
        session.rollback()
        print(f"❌ Error while seeding data: {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_sample_data()
