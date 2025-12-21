# app/api/games.py
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Game
from app.db.session import get_db
from app.schemas.games import GameRead

router = APIRouter(prefix="/games", tags=["games"])


@router.get("", response_model=List[GameRead])
def list_games(session: Session = Depends(get_db)) -> List[GameRead]:
    games = list(session.execute(select(Game).order_by(Game.name)).scalars().all())
    return [GameRead.from_orm(g) for g in games]
