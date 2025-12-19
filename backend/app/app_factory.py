from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import health, tasks
from app.core.config import APP_NAME, APP_VERSION
from app.core.db import init_db


def create_app(local: bool) -> FastAPI:
    init_db(local)
    app = FastAPI(title=APP_NAME, version=APP_VERSION)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(tasks.router)
    return app
