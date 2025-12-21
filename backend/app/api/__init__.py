# app/api/__init__.py
from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.battles import router as battles_router
from app.api.players import router as players_router
from app.api.stats import router as stats_router

api_router = APIRouter()
api_router.include_router(auth_router)

# Все “игровые данные” идут в контексте game_id
api_router.include_router(battles_router)
api_router.include_router(players_router)
api_router.include_router(stats_router)
