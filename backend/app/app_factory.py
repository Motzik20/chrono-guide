import os

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api.routers import health, schedule, settings, tasks, users
from app.core.config import APP_NAME, APP_VERSION
from app.core.db import init_db
from app.core.exceptions import NotFoundError, SystemError


def create_app(local: bool) -> FastAPI:
    init_db(local)
    app = FastAPI(title=APP_NAME, version=APP_VERSION)

    cors_origins_env = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000" if local else ""
    )

    allowed_origins = [
        origin.strip() for origin in cors_origins_env.split(",") if origin.strip()
    ]

    if not allowed_origins and not local:
        allowed_origins = []

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(NotFoundError)
    async def not_found_error_handler(
        _request: Request, exc: NotFoundError
    ) -> JSONResponse:
        """Handle NotFoundError exceptions - returns 404 Not Found."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(
        _request: Request, exc: ValidationError
    ) -> JSONResponse:
        """Handle ValidationError exceptions - returns 400 Bad Request."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.exception_handler(SystemError)
    async def system_error_handler(_request: Request, exc: SystemError) -> JSONResponse:
        """Handle SystemError exceptions - returns 500 Internal Server Error."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc)},
        )

    app.include_router(health.router)
    app.include_router(tasks.router)
    app.include_router(users.router)
    app.include_router(settings.router)
    app.include_router(schedule.router)
    assert app.exception_handlers[NotFoundError] is not_found_error_handler
    assert app.exception_handlers[ValidationError] is validation_error_handler
    assert app.exception_handlers[SystemError] is system_error_handler
    return app
