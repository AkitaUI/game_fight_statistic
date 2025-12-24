# app/api/__init__.py
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.auth import router as auth_router
from app.api.battles import router as battles_router
from app.api.games import router as games_router
from app.api.players import router as players_router
from app.api.stats import router as stats_router

from app.api.deps import get_current_user

api_router = APIRouter(prefix="/api")

# ✅ Публичные эндпоинты (регистрация/логин + /auth/me защищён сам по себе через Depends в auth.py)
api_router.include_router(auth_router)

# ✅ Всё остальное — не публичное (требует Bearer-токен)
protected = APIRouter(dependencies=[Depends(get_current_user)])
protected.include_router(games_router)
protected.include_router(players_router)
protected.include_router(battles_router)
protected.include_router(stats_router)

api_router.include_router(protected)
