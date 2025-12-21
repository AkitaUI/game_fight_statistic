"""multi-game + roles + align nullable/FKs/uniques

Revision ID: 0002_multi_game_and_roles
Revises: 0001_initial_schema
Create Date: 2025-12-22
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_multi_game_and_roles"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) games
    op.create_table(
        "games",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("slug", sa.String(length=64), nullable=False, unique=True),
        sa.Column("name", sa.String(length=128), nullable=False),
    )
    op.create_index("ix_games_slug", "games", ["slug"], unique=True)

    # Создаём "дефолтную" игру и берём её id
    conn = op.get_bind()
    conn.execute(sa.text("INSERT INTO games (slug, name) VALUES (:s, :n)"), {"s": "default", "n": "Default Game"})
    default_game_id = conn.execute(sa.text("SELECT id FROM games WHERE slug='default'")).scalar_one()

    # 2) users.role (Enum)
    op.execute("CREATE TYPE user_role AS ENUM ('player', 'analyst', 'admin')")
    op.add_column("users", sa.Column("role", sa.Enum("player", "analyst", "admin", name="user_role"), nullable=True))
    op.execute("UPDATE users SET role = 'player' WHERE role IS NULL")
    op.alter_column("users", "role", nullable=False, server_default=sa.text("'player'"))

    # 3) add game_id to core tables: players, maps, game_modes, weapons, battles, player_battle_stats
    op.add_column("players", sa.Column("game_id", sa.BigInteger(), nullable=True))
    op.add_column("maps", sa.Column("game_id", sa.BigInteger(), nullable=True))
    op.add_column("game_modes", sa.Column("game_id", sa.BigInteger(), nullable=True))
    op.add_column("weapons", sa.Column("game_id", sa.BigInteger(), nullable=True))
    op.add_column("battles", sa.Column("game_id", sa.BigInteger(), nullable=True))
    op.add_column("player_battle_stats", sa.Column("game_id", sa.BigInteger(), nullable=True))

    # Заполняем game_id старым данным (всё относим к default)
    conn.execute(sa.text("UPDATE players SET game_id = :gid WHERE game_id IS NULL"), {"gid": default_game_id})
    conn.execute(sa.text("UPDATE maps SET game_id = :gid WHERE game_id IS NULL"), {"gid": default_game_id})
    conn.execute(sa.text("UPDATE game_modes SET game_id = :gid WHERE game_id IS NULL"), {"gid": default_game_id})
    conn.execute(sa.text("UPDATE weapons SET game_id = :gid WHERE game_id IS NULL"), {"gid": default_game_id})
    conn.execute(sa.text("UPDATE battles SET game_id = :gid WHERE game_id IS NULL"), {"gid": default_game_id})
    conn.execute(sa.text("UPDATE player_battle_stats SET game_id = :gid WHERE game_id IS NULL"), {"gid": default_game_id})

    # Теперь делаем NOT NULL + FK + индексы
    # players.game_id
    op.create_index("ix_players_game_id", "players", ["game_id"])
    op.create_foreign_key("fk_players_game_id_games", "players", "games", ["game_id"], ["id"], ondelete="CASCADE")
    op.alter_column("players", "game_id", nullable=False)

    # maps.game_id
    op.create_index("ix_maps_game_id", "maps", ["game_id"])
    op.create_foreign_key("fk_maps_game_id_games", "maps", "games", ["game_id"], ["id"], ondelete="CASCADE")
    op.alter_column("maps", "game_id", nullable=False)

    # game_modes.game_id
    op.create_index("ix_game_modes_game_id", "game_modes", ["game_id"])
    op.create_foreign_key("fk_game_modes_game_id_games", "game_modes", "games", ["game_id"], ["id"], ondelete="CASCADE")
    op.alter_column("game_modes", "game_id", nullable=False)

    # weapons.game_id
    op.create_index("ix_weapons_game_id", "weapons", ["game_id"])
    op.create_foreign_key("fk_weapons_game_id_games", "weapons", "games", ["game_id"], ["id"], ondelete="CASCADE")
    op.alter_column("weapons", "game_id", nullable=False)

    # battles.game_id
    op.create_index("ix_battles_game_id", "battles", ["game_id"])
    op.create_foreign_key("fk_battles_game_id_games", "battles", "games", ["game_id"], ["id"], ondelete="CASCADE")
    op.alter_column("battles", "game_id", nullable=False)

    # player_battle_stats.game_id
    op.create_index("ix_player_battle_stats_game_id", "player_battle_stats", ["game_id"])
    op.create_foreign_key(
        "fk_player_battle_stats_game_id_games",
        "player_battle_stats",
        "games",
        ["game_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.alter_column("player_battle_stats", "game_id", nullable=False)

    # 4) Align nullable / ON DELETE with models

    # battles.map_id, battles.mode_id должны быть nullable=True и ON DELETE SET NULL
    # В Postgres имена FK обычно вида battles_map_id_fkey, battles_mode_id_fkey.
    op.drop_constraint("battles_map_id_fkey", "battles", type_="foreignkey")
    op.drop_constraint("battles_mode_id_fkey", "battles", type_="foreignkey")

    op.alter_column("battles", "map_id", nullable=True)
    op.alter_column("battles", "mode_id", nullable=True)

    op.create_foreign_key("battles_map_id_fkey", "battles", "maps", ["map_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("battles_mode_id_fkey", "battles", "game_modes", ["mode_id"], ["id"], ondelete="SET NULL")

    # player_battle_stats.team_id должен быть nullable=True и ON DELETE SET NULL (как в модели)
    op.drop_constraint("player_battle_stats_team_id_fkey", "player_battle_stats", type_="foreignkey")
    op.alter_column("player_battle_stats", "team_id", nullable=True)
    op.create_foreign_key(
        "player_battle_stats_team_id_fkey",
        "player_battle_stats",
        "battle_teams",
        ["team_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # 5) Update UNIQUE constraints under multi-game model
    # Было: nickname unique globally; нужно: (game_id, nickname)
    # Было: weapons.name unique globally; нужно: (game_id, name)
    # Было: maps.name не unique, но нам нужна уникальность внутри игры
    # Было: game_modes.code unique globally; нужно: (game_id, code)

    # players nickname unique (создано колонкой unique=True в 0001): players_nickname_key
    op.drop_constraint("players_nickname_key", "players", type_="unique")
    op.create_unique_constraint("uq_player_game_nickname", "players", ["game_id", "nickname"])

    # weapons name unique: weapons_name_key
    op.drop_constraint("weapons_name_key", "weapons", type_="unique")
    op.create_unique_constraint("uq_weapons_game_id_name", "weapons", ["game_id", "name"])

    # game_modes code unique: game_modes_code_key
    op.drop_constraint("game_modes_code_key", "game_modes", type_="unique")
    op.create_unique_constraint("uq_game_modes_game_id_code", "game_modes", ["game_id", "code"])

    # maps unique внутри игры
    # (в 0001 maps.name не unique, так что просто добавляем uq)
    op.create_unique_constraint("uq_maps_game_id_name", "maps", ["game_id", "name"])


def downgrade() -> None:
    # В downgrade делаем минимально обратимое, но учти:
    # если в реальности у тебя появятся данные по разным играм, откат потеряет смысл.

    op.drop_constraint("uq_maps_game_id_name", "maps", type_="unique")
    op.drop_constraint("uq_game_modes_game_id_code", "game_modes", type_="unique")
    op.drop_constraint("uq_weapons_game_id_name", "weapons", type_="unique")
    op.drop_constraint("uq_player_game_nickname", "players", type_="unique")

    op.create_unique_constraint("game_modes_code_key", "game_modes", ["code"])
    op.create_unique_constraint("weapons_name_key", "weapons", ["name"])
    op.create_unique_constraint("players_nickname_key", "players", ["nickname"])

    op.drop_constraint("player_battle_stats_team_id_fkey", "player_battle_stats", type_="foreignkey")
    op.alter_column("player_battle_stats", "team_id", nullable=False)
    op.create_foreign_key(
        "player_battle_stats_team_id_fkey",
        "player_battle_stats",
        "battle_teams",
        ["team_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("battles_map_id_fkey", "battles", type_="foreignkey")
    op.drop_constraint("battles_mode_id_fkey", "battles", type_="foreignkey")
    op.alter_column("battles", "map_id", nullable=False)
    op.alter_column("battles", "mode_id", nullable=False)
    op.create_foreign_key("battles_map_id_fkey", "battles", "maps", ["map_id"], ["id"])
    op.create_foreign_key("battles_mode_id_fkey", "battles", "game_modes", ["mode_id"], ["id"])

    op.drop_constraint("fk_player_battle_stats_game_id_games", "player_battle_stats", type_="foreignkey")
    op.drop_index("ix_player_battle_stats_game_id", table_name="player_battle_stats")
    op.drop_column("player_battle_stats", "game_id")

    op.drop_constraint("fk_battles_game_id_games", "battles", type_="foreignkey")
    op.drop_index("ix_battles_game_id", table_name="battles")
    op.drop_column("battles", "game_id")

    op.drop_constraint("fk_weapons_game_id_games", "weapons", type_="foreignkey")
    op.drop_index("ix_weapons_game_id", table_name="weapons")
    op.drop_column("weapons", "game_id")

    op.drop_constraint("fk_game_modes_game_id_games", "game_modes", type_="foreignkey")
    op.drop_index("ix_game_modes_game_id", table_name="game_modes")
    op.drop_column("game_modes", "game_id")

    op.drop_constraint("fk_maps_game_id_games", "maps", type_="foreignkey")
    op.drop_index("ix_maps_game_id", table_name="maps")
    op.drop_column("maps", "game_id")

    op.drop_constraint("fk_players_game_id_games", "players", type_="foreignkey")
    op.drop_index("ix_players_game_id", table_name="players")
    op.drop_column("players", "game_id")

    op.drop_column("users", "role")
    op.execute("DROP TYPE IF EXISTS user_role")

    op.drop_index("ix_games_slug", table_name="games")
    op.drop_table("games")
