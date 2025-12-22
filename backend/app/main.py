# app/main.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.views import router as views_router
from app.api.ui_proxy import router as ui_proxy_router

app.include_router(ui_proxy_router)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Game Battles Stats API",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
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
