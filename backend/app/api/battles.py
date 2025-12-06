# app/api/battles.py
from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BattleNotFoundError,
    BattleAlreadyFinishedError,
    InvalidBattleOperationError,
    PlayerNotFoundError,
)
from app.db.session import get_session
from app.schemas.base import PagedResponse
from app.schemas.battle import (
    BattleCreate,
    BattleRead,
    BattleListItem,
    BattleTeamCreate,
    BattleTeamRead,
    PlayerBattleStatsCreate,
    PlayerBattleStatsRead,
    BattleFinishRequest,
)
from app.services import BattleService

router = APIRouter()


@router.post(
    "",
    response_model=BattleRead,
    status_code=status.HTTP_201_CREATED,
)
def create_battle(
    battle_in: BattleCreate,
    session: Session = Depends(get_session),
) -> BattleRead:
    service = BattleService(session)
    return service.create_battle(battle_in)


@router.get(
    "/{battle_id}",
    response_model=BattleRead,
)
def get_battle(
    battle_id: int,
    session: Session = Depends(get_session),
) -> BattleRead:
    service = BattleService(session)
    try:
        return service.get_battle_details(battle_id)
    except BattleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "",
    response_model=PagedResponse,
)
def list_battles(
    player_id: Optional[int] = Query(None),
    map_id: Optional[int] = Query(None),
    mode_id: Optional[int] = Query(None),
    is_ranked: Optional[bool] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    session: Session = Depends(get_session),
):
    service = BattleService(session)
    battles: List[BattleListItem] = service.list_battles(
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


@router.post(
    "/{battle_id}/teams",
    response_model=BattleTeamRead,
    status_code=status.HTTP_201_CREATED,
)
def add_team(
    battle_id: int,
    team_in: BattleTeamCreate,
    session: Session = Depends(get_session),
) -> BattleTeamRead:
    service = BattleService(session)
    try:
        return service.add_team_to_battle(battle_id, team_in)
    except BattleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except BattleAlreadyFinishedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/{battle_id}/players",
    response_model=PlayerBattleStatsRead,
    status_code=status.HTTP_201_CREATED,
)
def add_player_stats(
    battle_id: int,
    stats_in: PlayerBattleStatsCreate,
    session: Session = Depends(get_session),
) -> PlayerBattleStatsRead:
    service = BattleService(session)
    try:
        return service.add_player_stats(battle_id, stats_in)
    except BattleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PlayerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except BattleAlreadyFinishedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except InvalidBattleOperationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/{battle_id}/finish",
    response_model=BattleRead,
)
def finish_battle(
    battle_id: int,
    body: BattleFinishRequest,
    session: Session = Depends(get_session),
) -> BattleRead:
    service = BattleService(session)
    try:
        return service.finish_battle(battle_id, body.ended_at)
    except BattleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except BattleAlreadyFinishedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
