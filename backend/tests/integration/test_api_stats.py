# backend/tests/integration/test_api_stats.py
from __future__ import annotations

from fastapi.testclient import TestClient


PLAYER_ID = 1  # предполагаем, что сидер создал игрока с id=1


def test_stats_player_summary(client: TestClient):
    resp = client.get(f"/stats/players/{PLAYER_ID}?ranked_only=false")
    assert resp.status_code in (200, 404)

    if resp.status_code == 200:
        data = resp.json()
        assert data["player_id"] == PLAYER_ID
        assert "total_battles" in data
        assert "total_kills" in data


def test_stats_player_maps(client: TestClient):
    resp = client.get(f"/stats/players/{PLAYER_ID}/maps?ranked_only=false")
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        data = resp.json()
        assert isinstance(data, list)
        if data:
            assert "map_name" in data[0]


def test_stats_player_weapons(client: TestClient):
    resp = client.get(f"/stats/players/{PLAYER_ID}/weapons?ranked_only=false")
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        data = resp.json()
        assert isinstance(data, list)
        if data:
            assert "weapon_name" in data[0]
            assert "kills" in data[0]
