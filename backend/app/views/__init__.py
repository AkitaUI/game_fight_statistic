# app/views/__init__.py
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/views/templates")


def _common_context(request: Request, page_title: str) -> dict:
    return {
        "request": request,
        "page_title": page_title,
        # можно расширять по мере надобности
        "enable_auth_ui": True,
        "enable_game_selector": True,
    }


@router.get("/", name="index", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "base.html",
        _common_context(request, "Game Stats"),
    )


@router.get("/players-ui", name="players_page", response_class=HTMLResponse)
def players_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "players.html",
        _common_context(request, "Players"),
    )


@router.get("/battles-ui", name="battles_page", response_class=HTMLResponse)
def battles_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "battles.html",
        _common_context(request, "Battles"),
    )


@router.get("/stats", name="stats_page", response_class=HTMLResponse)
def stats_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "stats.html",
        _common_context(request, "Stats"),
    )
