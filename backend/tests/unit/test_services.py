# backend/tests/unit/test_models.py
from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import select

from app.db.models import Player, Battle, PlayerBattleStats, BattleTeam


def test_create_player_and_battle(db_session):
    # Уникальный ник, чтобы не пересекаться с реальными данными
    nickname = f"TestPlayer_{uuid.uuid4().hex[:8]}"

    player = Player(nickname=nickname)
    db_session.add(player)
    db_session.flush()  # чтобы проставился id

    battle = Battle(
        started_at=datetime.utcnow(),
        is_ranked=True,
        map_id=1,    # предполагаем, что в сидере есть карта с id=1
        mode_id=1,   # и режим с id=1
    )
    db_session.add(battle)
    db_session.flush()

    team = BattleTeam(
        battle_id=battle.id,
        team_index=1,
        name="Red",
        is_winner=True,
    )
    db_session.add(team)
    db_session.flush()

    stats = PlayerBattleStats(
        battle_id=battle.id,
        player_id=player.id,
        team_id=team.id,
        kills=10,
        deaths=5,
        assists=2,
        damage_dealt=1000,
        damage_taken=500,
        score=1500,
        headshots=3,
        result=1,
    )
    db_session.add(stats)
    db_session.commit()

    stmt = select(PlayerBattleStats).where(PlayerBattleStats.id == stats.id)
    loaded = db_session.execute(stmt).scalar_one()

    assert loaded.player.nickname == nickname
    assert loaded.battle.is_ranked is True
    assert loaded.team.name == "Red"
    assert loaded.kills == 10
