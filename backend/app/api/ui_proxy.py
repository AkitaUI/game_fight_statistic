# app/api/ui_proxy.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.base import PagedResponse
from app.schemas.player import PlayerListItem, PlayerWithStatsSummary
from app.schemas.battle import BattleListItem, BattleRead
from app.schemas.stats import MapStatsItem, WeaponStatsItem
from app.schemas.player import PlayerStatsSummary  # если у тебя summary тут
from app.services.player_service import PlayerService
from app.services.battle_service import BattleService
from app.services.stats_service import StatsService  # если есть

router = APIRouter(tags=["ui-proxy"])

DEFAULT_GAME_ID = 1  # можешь потом сделать выбор игры на UI

@router.get("/players", response_model=PagedResponse)
def ui_list_players(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    session: Session = Depends(get_db),
):
    service = PlayerService(session)
    items = service.list_players(game_id=DEFAULT_GAME_ID, offset=offset, limit=limit)
    total = len(items) if offset == 0 else offset + len(items)
    return PagedResponse(total=total, items=items)

@router.get("/players/{player_id}/summary", response_model=PlayerWithStatsSummary)
def ui_player_summary(
    player_id: int,
    session: Session = Depends(get_db),
):
    service = PlayerService(session)
    # filters у тебя сейчас формируются в api/players.py, но тут можно пустой
    from app.schemas.stats import PlayerStatsFilter
    filters = PlayerStatsFilter(date_from=None, date_to=None, map_ids=None, mode_ids=None, ranked_only=None)
    return service.get_player_stats_summary(game_id=DEFAULT_GAME_ID, player_id=player_id, filters=filters)

@router.get("/battles", response_model=PagedResponse)
def ui_list_battles(
    player_id: int | None = Query(None),
    is_ranked: bool | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    session: Session = Depends(get_db),
):
    service = BattleService(session)
    items = service.list_battles(
        game_id=DEFAULT_GAME_ID,
        player_id=player_id,
        is_ranked=is_ranked,
        offset=offset,
        limit=limit,
    )
    total = len(items) if offset == 0 else offset + len(items)
    return PagedResponse(total=total, items=items)

@router.get("/battles/{battle_id}", response_model=BattleRead)
def ui_battle_details(
    battle_id: int,
    session: Session = Depends(get_db),
):
    service = BattleService(session)
    return service.get_battle_details(game_id=DEFAULT_GAME_ID, battle_id=battle_id)

@router.get("/stats/players/{player_id}", response_model=PlayerStatsSummary)
def ui_stats_player_summary(
    player_id: int,
    ranked_only: bool | None = Query(None),
    session: Session = Depends(get_db),
):
    service = StatsService(session)
    from app.schemas.stats import PlayerStatsFilter
    filters = PlayerStatsFilter(date_from=None, date_to=None, map_ids=None, mode_ids=None, ranked_only=ranked_only)
    return service.get_player_summary(game_id=DEFAULT_GAME_ID, player_id=player_id, filters=filters)

@router.get("/stats/players/{player_id}/maps", response_model=list[MapStatsItem])
def ui_stats_player_maps(
    player_id: int,
    ranked_only: bool | None = Query(None),
    session: Session = Depends(get_db),
):
    service = StatsService(session)
    from app.schemas.stats import PlayerStatsFilter
    filters = PlayerStatsFilter(date_from=None, date_to=None, map_ids=None, mode_ids=None, ranked_only=ranked_only)
    return service.get_player_map_stats(game_id=DEFAULT_GAME_ID, player_id=player_id, filters=filters)

@router.get("/stats/players/{player_id}/weapons", response_model=list[WeaponStatsItem])
def ui_stats_player_weapons(
    player_id: int,
    ranked_only: bool | None = Query(None),
    session: Session = Depends(get_db),
):
    service = StatsService(session)
    from app.schemas.stats import PlayerStatsFilter
    filters = PlayerStatsFilter(date_from=None, date_to=None, map_ids=None, mode_ids=None, ranked_only=ranked_only)
    return service.get_player_weapon_stats(game_id=DEFAULT_GAME_ID, player_id=player_id, filters=filters)
