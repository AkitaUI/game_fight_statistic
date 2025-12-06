# app/api/__init__.py
from fastapi import APIRouter

from . import players, battles, stats

api_router = APIRouter()
api_router.include_router(players.router, prefix="/players", tags=["players"])
api_router.include_router(battles.router, prefix="/battles", tags=["battles"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
