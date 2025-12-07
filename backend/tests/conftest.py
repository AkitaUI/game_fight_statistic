# backend/tests/conftest.py
from __future__ import annotations

from collections.abc import Generator
import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# ---------------- PYTHONPATH ----------------

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.main import app
from app.db.session import SessionLocal, get_session as app_get_session


# ---------------- ФИКСТУРЫ БД ----------------

@pytest.fixture(scope="session", autouse=True)
def prepare_test_db() -> Generator[None, None, None]:
    """
    Для простоты: считаем, что миграции уже прогнаны,
    структура БД готова. Ничего не создаём/не дропаем.
    """
    yield


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """
    Сессия к реальному Postgres (как у приложения).
    Для простоты — без транзакционного отката, т.к.
    проект учебный и объём данных небольшой.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------- FastAPI TestClient ----------

def _override_get_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[app_get_session] = _override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
