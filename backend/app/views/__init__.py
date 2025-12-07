# app/views/__init__.py
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="app/views/templates")


@router.get("/", name="index", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """
    Главная страница — простая заглушка.
    Можно перенаправлять пользователя к разделу Players.
    """
    return templates.TemplateResponse(
        "base.html",
        {
            "request": request,
            "page_title": "Game Stats",
        },
    )


@router.get("/players-ui", name="players_page", response_class=HTMLResponse)
def players_page(request: Request) -> HTMLResponse:
    """
    HTML-страница списка игроков.

    JSON-API по-прежнему доступен по /players,
    эта страница просто использует его через JS.
    """
    return templates.TemplateResponse(
        "players.html",
        {
            "request": request,
            "page_title": "Players",
        },
    )


@router.get("/battles-ui", name="battles_page", response_class=HTMLResponse)
def battles_page(request: Request) -> HTMLResponse:
    """
    HTML-страница списка боёв.

    JSON-API по-прежнему доступен по /battles,
    а страница подтягивает данные через JS.
    """
    return templates.TemplateResponse(
        "battles.html",
        {
            "request": request,
            "page_title": "Battles",
        },
    )


@router.get("/stats", name="stats_page", response_class=HTMLResponse)
def stats_page(request: Request) -> HTMLResponse:
    """
    HTML-страница статистики игрока (как у тебя уже было).
    """
    return templates.TemplateResponse(
        "stats.html",
        {
            "request": request,
            "page_title": "Stats",
        },
    )
