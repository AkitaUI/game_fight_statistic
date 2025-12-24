# app/api/stats.py
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import PlayerNotFoundError
from app.db.session import get_db
from app.schemas.player import PlayerStatsSummary
from app.schemas.stats import MapStatsItem, PlayerStatsFilter, WeaponStatsItem
from app.services.stats_service import StatsService

router = APIRouter(prefix="/games/{game_id}/stats", tags=["stats"])


@router.get(
    "/players/{player_id}",
    response_model=PlayerStatsSummary,
    dependencies=[Depends(get_current_user)],  # ✅ любой авторизованный
)
def get_player_summary(
    game_id: int,
    player_id: int,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    map_ids: Optional[List[int]] = Query(None),
    mode_ids: Optional[List[int]] = Query(None),
    ranked_only: Optional[bool] = Query(None),
    session: Session = Depends(get_db),
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
        return service.get_player_summary(game_id=game_id, player_id=player_id, filters=filters)
    except PlayerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get(
    "/players/{player_id}/maps",
    response_model=List[MapStatsItem],
    dependencies=[Depends(get_current_user)],  # ✅ любой авторизованный
)
def get_player_map_stats(
    game_id: int,
    player_id: int,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    map_ids: Optional[List[int]] = Query(None),
    mode_ids: Optional[List[int]] = Query(None),
    ranked_only: Optional[bool] = Query(None),
    session: Session = Depends(get_db),
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
        return service.get_player_map_stats(game_id=game_id, player_id=player_id, filters=filters)
    except PlayerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get(
    "/players/{player_id}/weapons",
    response_model=List[WeaponStatsItem],
    dependencies=[Depends(get_current_user)],  # ✅ любой авторизованный
)
def get_player_weapon_stats(
    game_id: int,
    player_id: int,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    map_ids: Optional[List[int]] = Query(None),
    mode_ids: Optional[List[int]] = Query(None),
    ranked_only: Optional[bool] = Query(None),
    session: Session = Depends(get_db),
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
        return service.get_player_weapon_stats(game_id=game_id, player_id=player_id, filters=filters)
    except PlayerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
