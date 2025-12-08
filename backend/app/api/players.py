# app/api/players.py
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import (
    PlayerNotFoundError,
    PlayerAlreadyExistsError,
)
from app.db.session import get_session
from app.schemas.player import (
    PlayerCreate,
    PlayerRead,
    PlayerListItem,
    PlayerWithStatsSummary,
)
from app.schemas.base import PagedResponse
from app.schemas.stats import PlayerStatsFilter
from app.services import PlayerService

router = APIRouter()


@router.post(
    "",
    response_model=PlayerRead,
    status_code=status.HTTP_201_CREATED,
)
def create_player(
    player_in: PlayerCreate,
    session: Session = Depends(get_session),
) -> PlayerRead:
    service = PlayerService(session)
    try:
        return service.create_player(player_in)
    except PlayerAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get(
    "/{player_id}",
    response_model=PlayerRead,
)
def get_player(
    player_id: int,
    session: Session = Depends(get_session),
) -> PlayerRead:
    service = PlayerService(session)
    try:
        return service.get_player(player_id)
    except PlayerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "",
    response_model=PagedResponse,
)
def list_players(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    session: Session = Depends(get_session),
):
    service = PlayerService(session)
    items: List[PlayerListItem] = service.list_players(offset=offset, limit=limit)
    total = len(items) if offset == 0 else offset + len(items)
    return PagedResponse(total=total, items=items)


@router.delete(
    "/{player_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_player(
    player_id: int,
    session: Session = Depends(get_session),
):
    service = PlayerService(session)
    try:
        service.delete_player(player_id)
    except PlayerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/{player_id}/summary",
    response_model=PlayerWithStatsSummary,
)
def get_player_summary(
    player_id: int,
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    map_ids: list[int] | None = Query(None),
    mode_ids: list[int] | None = Query(None),
    ranked_only: bool | None = Query(None),
    session: Session = Depends(get_session),
):
    filters = PlayerStatsFilter(
        date_from=None,
        date_to=None,
        map_ids=map_ids,
        mode_ids=mode_ids,
        ranked_only=ranked_only,
    )
    service = PlayerService(session)
    try:
        return service.get_player_stats_summary(player_id, filters)
    except PlayerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
