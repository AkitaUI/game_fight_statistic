# app/api/battles.py
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BattleAlreadyFinishedError,
    BattleNotFoundError,
    InvalidBattleOperationError,
    PlayerNotFoundError,
)
from app.db.session import get_db
from app.schemas.base import PagedResponse
from app.schemas.battle import BattleCreate, BattleFinishRequest, BattleListItem, BattleRead
from app.services.battle_service import BattleService

router = APIRouter(prefix="/games/{game_id}/battles", tags=["battles"])


@router.post("", response_model=BattleRead, status_code=status.HTTP_201_CREATED)
def create_battle(
    game_id: int,
    battle_in: BattleCreate,
    session: Session = Depends(get_db),
) -> BattleRead:
    service = BattleService(session)
    return service.create_battle(game_id=game_id, data=battle_in)


@router.get("/{battle_id}", response_model=BattleRead)
def get_battle(
    game_id: int,
    battle_id: int,
    session: Session = Depends(get_db),
) -> BattleRead:
    service = BattleService(session)
    try:
        return service.get_battle_details(game_id=game_id, battle_id=battle_id)
    except BattleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("", response_model=PagedResponse)
def list_battles(
    game_id: int,
    player_id: Optional[int] = Query(None),
    map_id: Optional[int] = Query(None),
    mode_id: Optional[int] = Query(None),
    is_ranked: Optional[bool] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    session: Session = Depends(get_db),
):
    service = BattleService(session)
    battles: List[BattleListItem] = service.list_battles(
        game_id=game_id,
        player_id=player_id,
        map_id=map_id,
        mode_id=mode_id,
        is_ranked=is_ranked,
        date_from=date_from,
        date_to=date_to,
        offset=offset,
        limit=limit,
    )
    total = len(battles) if offset == 0 else offset + len(battles)
    return PagedResponse(total=total, items=battles)


@router.post("/{battle_id}/finish", response_model=BattleRead)
def finish_battle(
    game_id: int,
    battle_id: int,
    body: BattleFinishRequest,
    session: Session = Depends(get_db),
) -> BattleRead:
    service = BattleService(session)
    try:
        return service.finish_battle(game_id=game_id, battle_id=battle_id, ended_at=body.ended_at)
    except BattleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except BattleAlreadyFinishedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except InvalidBattleOperationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except PlayerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
