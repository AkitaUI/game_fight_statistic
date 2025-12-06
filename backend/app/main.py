# app/main.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.views import router as views_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Game Battles Stats API",
        version="1.0.0",
    )

    # CORS — чтобы при необходимости можно было ходить к API с внешнего фронта
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],          # при желании можно сузить список доменов
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # REST API (JSON)
    app.include_router(api_router)

    # HTML-страницы (клиентское представление)
    app.include_router(views_router)

    # Статические файлы (CSS, JS, изображения)
    app.mount(
        "/static",
        StaticFiles(directory="app/views/static"),
        name="static",
    )

    return app


app = create_app()
