# app/main.py
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.exceptions import PlayerNotFoundError

from app.api import api_router
from app.views import router as views_router
from app.api.ui_proxy import router as ui_proxy_router

from app.core.seed import seed_initial_admin
from app.db.session import SessionLocal  # если у тебя так называется фабрика сессий



def create_app() -> FastAPI:
    app = FastAPI(
        title="Game Battles Stats API",
        version="1.0.0",
    )

    app.include_router(ui_proxy_router)

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

    
    @app.exception_handler(PlayerNotFoundError)
    async def player_not_found_handler(request: Request, exc: PlayerNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc)},
    )

    return app

@app.on_event("startup")
def _seed_admin_on_startup() -> None:
    db = SessionLocal()
    try:
        seed_initial_admin(db)
    finally:
        db.close()
        
app = create_app()
