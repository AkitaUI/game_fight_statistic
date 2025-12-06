# app/api/stats.py
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.exceptions import PlayerNotFoundError
from app.db.session import get_session
from app.schemas.player import PlayerStatsSummary
from app.schemas.stats import (
    PlayerStatsFilter,
    MapStatsItem,
    WeaponStatsItem,
    ModeStatsItem,
    GlobalStatsFilter,
)
from app.services import StatsService

router = APIRouter()


@router.get(
    "/players/{player_id}",
    response_model=PlayerStatsSummary,
)
def get_player_summary(
    player_id: int,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    map_ids: Optional[List[int]] = Query(None),
    mode_ids: Optional[List[int]] = Query(None),
    ranked_only: Optional[bool] = Query(None),
    session: Session = Depends(get_session),
) -> PlayerStatsSummary:
    filters = PlayerStatsFilter(
        date_from=date_from,
        date_to=date_to,
        map_ids=map_ids,
        mode_ids=mode_ids,
        ranked_only=ranked_only,
    )
    service = StatsService(session)
    try:
        return service.get_player_summary(player_id, filters)
    except PlayerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get(
    "/players/{player_id}/maps",
    response_model=List[MapStatsItem],
)
def get_player_map_stats(
    player_id: int,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    map_ids: Optional[List[int]] = Query(None),
    mode_ids: Optional[List[int]] = Query(None),
    ranked_only: Optional[bool] = Query(None),
    session: Session = Depends(get_session),
) -> List[MapStatsItem]:
    filters = PlayerStatsFilter(
        date_from=date_from,
        date_to=date_to,
        map_ids=map_ids,
        mode_ids=mode_ids,
        ranked_only=ranked_only,
    )
    service = StatsService(session)
    try:
        return service.get_player_map_stats(player_id, filters)
    except PlayerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get(
    "/players/{player_id}/weapons",
    response_model=List[WeaponStatsItem],
)
def get_player_weapon_stats(
    player_id: int,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    map_ids: Optional[List[int]] = Query(None),
    mode_ids: Optional[List[int]] = Query(None),
    ranked_only: Optional[bool] = Query(None),
    session: Session = Depends(get_session),
) -> List[WeaponStatsItem]:
    filters = PlayerStatsFilter(
        date_from=date_from,
        date_to=date_to,
        map_ids=map_ids,
        mode_ids=mode_ids,
        ranked_only=ranked_only,
    )
    service = StatsService(session)
    try:
        return service.get_player_weapon_stats(player_id, filters)
    except PlayerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get(
    "/global/maps",
    response_model=List[MapStatsItem],
)
def get_global_map_stats(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    ranked_only: Optional[bool] = Query(None),
    session: Session = Depends(get_session),
) -> List[MapStatsItem]:
    filters = GlobalStatsFilter(
        date_from=date_from,
        date_to=date_to,
        ranked_only=ranked_only,
    )
    service = StatsService(session)
    return service.get_global_map_stats(filters)


@router.get(
    "/global/modes",
    response_model=List[ModeStatsItem],
)
def get_global_mode_stats(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    ranked_only: Optional[bool] = Query(None),
    session: Session = Depends(get_session),
) -> List[ModeStatsItem]:
    filters = GlobalStatsFilter(
        date_from=date_from,
        date_to=date_to,
        ranked_only=ranked_only,
    )
    service = StatsService(session)
    return service.get_global_mode_stats(filters)
