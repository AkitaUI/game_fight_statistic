# app/api/players.py
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import PlayerAlreadyExistsError, PlayerNotFoundError
from app.db.session import get_db
from app.schemas.base import PagedResponse
from app.schemas.player import PlayerCreate, PlayerListItem, PlayerRead, PlayerWithStatsSummary
from app.schemas.stats import PlayerStatsFilter
from app.services.player_service import PlayerService

router = APIRouter(prefix="/games/{game_id}/players", tags=["players"])


@router.post("", response_model=PlayerRead, status_code=status.HTTP_201_CREATED)
def create_player(
    game_id: int,
    player_in: PlayerCreate,
    session: Session = Depends(get_db),
) -> PlayerRead:
    service = PlayerService(session)
    try:
        return service.create_player(game_id=game_id, data=player_in)
    except PlayerAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("/{player_id}", response_model=PlayerRead)
def get_player(
    game_id: int,
    player_id: int,
    session: Session = Depends(get_db),
) -> PlayerRead:
    service = PlayerService(session)
    try:
        return service.get_player(game_id=game_id, player_id=player_id)
    except PlayerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("", response_model=PagedResponse)
def list_players(
    game_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    session: Session = Depends(get_db),
):
    service = PlayerService(session)
    items: List[PlayerListItem] = service.list_players(game_id=game_id, offset=offset, limit=limit)
    total = len(items) if offset == 0 else offset + len(items)
    return PagedResponse(total=total, items=items)


@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player(
    game_id: int,
    player_id: int,
    session: Session = Depends(get_db),
):
    service = PlayerService(session)
    try:
        service.delete_player(game_id=game_id, player_id=player_id)
    except PlayerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{player_id}/summary", response_model=PlayerWithStatsSummary)
def get_player_summary(
    game_id: int,
    player_id: int,
    map_ids: list[int] | None = Query(None),
    mode_ids: list[int] | None = Query(None),
    ranked_only: bool | None = Query(None),
    session: Session = Depends(get_db),
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
        return service.get_player_stats_summary(game_id=game_id, player_id=player_id, filters=filters)
    except PlayerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
