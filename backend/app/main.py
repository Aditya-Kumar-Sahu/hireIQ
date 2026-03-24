"""
FastAPI application factory and entrypoint.

Configures:
- CORS middleware for the Next.js frontend
- Global exception handling for consistent API envelope responses
- Lifespan events for DB engine and Redis connection lifecycle
- API router mounting for v1 endpoints
- Health check route
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.dependencies import DBSession
from app.api.v1.routes import router as api_v1_router
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import HireIQException
from app.core.redis import close_redis, redis_client

logger = logging.getLogger(__name__)


# ── Lifespan ───────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and shutdown events.

    Startup: log that the application is ready.
    Shutdown: dispose the async DB engine and close Redis.
    """
    logger.info("🚀 HireIQ backend starting up (v%s)", settings.APP_VERSION)
    yield
    await engine.dispose()
    await close_redis()
    logger.info("🛑 HireIQ backend shut down gracefully")


# ── App Factory ────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-Powered Hiring Copilot — autonomous recruitment agents",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ───────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Global Exception Handler ───────────────────────────────────
    @app.exception_handler(HireIQException)
    async def hireiq_exception_handler(
        request: Request,
        exc: HireIQException,
    ) -> JSONResponse:
        """Convert application exceptions into structured API envelope."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "data": None,
                "error": exc.message,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Catch-all for unexpected errors — never leak stack traces."""
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "data": None,
                "error": "Internal server error",
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Return request validation issues in the standard response envelope."""
        errors = [
            f"{'.'.join(str(part) for part in err['loc'])}: {err['msg']}"
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "data": None,
                "error": "; ".join(errors),
            },
        )

    # ── Health Check ───────────────────────────────────────────────
    @app.get("/health", tags=["Health"], response_model=None)
    async def health_check(db: DBSession) -> dict[str, object] | JSONResponse:
        """Health check endpoint that validates database and Redis connectivity."""
        checks: dict[str, str] = {}
        failures: list[str] = []

        try:
            await db.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception:
            logger.exception("Health check database probe failed")
            checks["database"] = "error"
            failures.append("database")

        try:
            await redis_client.ping()
            checks["redis"] = "ok"
        except Exception:
            logger.exception("Health check redis probe failed")
            checks["redis"] = "error"
            failures.append("redis")

        payload = {
            "status": "healthy" if not failures else "unhealthy",
            "version": settings.APP_VERSION,
            "checks": checks,
        }
        if failures:
            return JSONResponse(status_code=503, content=payload)
        return payload

    # ── API Routes ─────────────────────────────────────────────────
    app.include_router(api_v1_router, prefix="/api/v1")

    return app


# ── Application Instance ──────────────────────────────────────────────
app = create_app()
