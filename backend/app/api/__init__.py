# app/api/__init__.py
from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.games import router as games_router
from app.api.battles import router as battles_router
from app.api.players import router as players_router
from app.api.stats import router as stats_router

api_router = APIRouter(prefix="/api")

# Auth
api_router.include_router(auth_router)

# Games directory (list games for selection in UI)
api_router.include_router(games_router)

# Game-scoped endpoints
api_router.include_router(battles_router)
api_router.include_router(players_router)
api_router.include_router(stats_router)
