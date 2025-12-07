# backend/tests/integration/test_api_battles.py
from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_battles_ok(client: TestClient):
    resp = client.get("/battles?offset=0&limit=10")
    assert resp.status_code == 200

    data = resp.json()
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)
