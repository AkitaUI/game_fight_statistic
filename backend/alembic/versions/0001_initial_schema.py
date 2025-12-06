# backend/alembic/versions/0001_initial_schema.py
"""initial schema

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2024-01-01 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("username", sa.String(length=32), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )

    # --- players ---
    op.create_table(
        "players",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("nickname", sa.String(length=50), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_players_user_id", "players", ["user_id"])

    # --- maps ---
    op.create_table(
        "maps",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.create_index("ix_maps_name", "maps", ["name"])

    # --- game_modes ---
    op.create_table(
        "game_modes",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )

    # --- weapons ---
    op.create_table(
        "weapons",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("category", sa.String(length=50), nullable=True),
    )

    # --- battles ---
    op.create_table(
        "battles",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("map_id", sa.BigInteger(), sa.ForeignKey("maps.id"), nullable=False),
        sa.Column("mode_id", sa.BigInteger(), sa.ForeignKey("game_modes.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("external_match_id", sa.String(length=100), nullable=True),
        sa.Column("is_ranked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_battles_map_id", "battles", ["map_id"])
    op.create_index("ix_battles_mode_id", "battles", ["mode_id"])
    op.create_index("ix_battles_started_at", "battles", ["started_at"])

    # --- battle_teams ---
    op.create_table(
        "battle_teams",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("battle_id", sa.BigInteger(), sa.ForeignKey("battles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("team_index", sa.SmallInteger(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("is_winner", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("battle_id", "team_index", name="uq_battle_team_index"),
    )
    op.create_index("ix_battle_teams_battle_id", "battle_teams", ["battle_id"])

    # --- player_battle_stats ---
    op.create_table(
        "player_battle_stats",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("battle_id", sa.BigInteger(), sa.ForeignKey("battles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("player_id", sa.BigInteger(), sa.ForeignKey("players.id", ondelete="CASCADE"), nullable=False),
        sa.Column("team_id", sa.BigInteger(), sa.ForeignKey("battle_teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kills", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deaths", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("assists", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("damage_dealt", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("damage_taken", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("headshots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("result", sa.SmallInteger(), nullable=False, server_default="0"),  # -1,0,1
        sa.Column("joined_at", sa.DateTime(), nullable=True),
        sa.Column("left_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("battle_id", "player_id", name="uq_battle_player"),
    )
    op.create_index("ix_player_battle_stats_battle_id", "player_battle_stats", ["battle_id"])
    op.create_index("ix_player_battle_stats_player_id", "player_battle_stats", ["player_id"])
    op.create_index("ix_player_battle_stats_team_id", "player_battle_stats", ["team_id"])

    # --- weapon_stats ---
    op.create_table(
        "weapon_stats",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "player_battle_stats_id",
            sa.BigInteger(),
            sa.ForeignKey("player_battle_stats.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("weapon_id", sa.BigInteger(), sa.ForeignKey("weapons.id"), nullable=False),
        sa.Column("shots_fired", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("kills", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("headshots", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("player_battle_stats_id", "weapon_id", name="uq_weapon_in_participation"),
    )
    op.create_index(
        "ix_weapon_stats_player_battle_stats_id",
        "weapon_stats",
        ["player_battle_stats_id"],
    )
    op.create_index("ix_weapon_stats_weapon_id", "weapon_stats", ["weapon_id"])
    

def downgrade() -> None:
    # Обратный порядок (FK-зависимости)
    op.drop_index("ix_weapon_stats_weapon_id", table_name="weapon_stats")
    op.drop_index("ix_weapon_stats_player_battle_stats_id", table_name="weapon_stats")
    op.drop_table("weapon_stats")

    op.drop_index("ix_player_battle_stats_team_id", table_name="player_battle_stats")
    op.drop_index("ix_player_battle_stats_player_id", table_name="player_battle_stats")
    op.drop_index("ix_player_battle_stats_battle_id", table_name="player_battle_stats")
    op.drop_table("player_battle_stats")

    op.drop_index("ix_battle_teams_battle_id", table_name="battle_teams")
    op.drop_table("battle_teams")

    op.drop_index("ix_battles_started_at", table_name="battles")
    op.drop_index("ix_battles_mode_id", table_name="battles")
    op.drop_index("ix_battles_map_id", table_name="battles")
    op.drop_table("battles")

    op.drop_table("weapons")
    op.drop_table("game_modes")

    op.drop_index("ix_maps_name", table_name="maps")
    op.drop_table("maps")

    op.drop_index("ix_players_user_id", table_name="players")
    op.drop_table("players")

    op.drop_table("users")
