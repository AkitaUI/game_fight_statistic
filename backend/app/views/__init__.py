# app/views/__init__.py
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Путь к шаблонам — относительно корня backend-приложения
templates = Jinja2Templates(directory="app/views/templates")

router = APIRouter()


@router.get("/", response_class=HTMLResponse, name="index")
async def index(request: Request) -> HTMLResponse:
    """
    Главная страница — просто редирект-подобный вариант:
    показываем небольшой дэшборд или ссылку на разделы.
    Для простоты – меню + приветствие.
    """
    return templates.TemplateResponse(
        "base.html",
        {
            "request": request,
            "page_title": "Game Stats – Home",
            "content_template": None,  # базовый шаблон сам покажет заглушку
        },
    )


@router.get("/players", response_class=HTMLResponse, name="players_page")
async def players_page(request: Request) -> HTMLResponse:
    """
    Страница списка игроков.
    Данные подтягиваются через JS из REST API (/players).
    """
    return templates.TemplateResponse(
        "players.html",
        {
            "request": request,
            "page_title": "Players",
        },
    )


@router.get("/battles", response_class=HTMLResponse, name="battles_page")
async def battles_page(request: Request) -> HTMLResponse:
    """
    Страница списка боёв.
    """
    return templates.TemplateResponse(
        "battles.html",
        {
            "request": request,
            "page_title": "Battles",
        },
    )


@router.get("/stats", response_class=HTMLResponse, name="stats_page")
async def stats_page(request: Request) -> HTMLResponse:
    """
    Страница аналитики.
    Здесь можно ввести ID игрока и увидеть его статистику,
    а также вставить ссылку/iframe на Grafana.
    """
    return templates.TemplateResponse(
        "stats.html",
        {
            "request": request,
            "page_title": "Player Stats",
        },
    )
