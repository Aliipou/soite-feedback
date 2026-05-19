"""FastAPI application factory with all middleware, routers, and lifecycle hooks."""

import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import structlog
import structlog.stdlib
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import settings
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routers import admin, auth, dashboard, public

# ── Logging configuration ─────────────────────────────────────────────────────

def _configure_logging() -> None:
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    if settings.environment == "development":
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


_configure_logging()
logger = structlog.get_logger()


# ── Rate limiter ──────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


# ── Application lifespan ──────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup checks and graceful shutdown."""
    logger.info("startup", version=settings.app_version, env=settings.environment)
    yield
    # Cancel background tasks on shutdown
    tasks = [t for t in asyncio.all_tasks() if t.get_name().startswith("background_")]
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("shutdown")


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Construct and return the FastAPI application."""
    app = FastAPI(
        title="Soite Kotikuntoutus Feedback API",
        version=settings.app_version,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        lifespan=lifespan,
    )

    # ── Rate limiting ─────────────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    app.add_middleware(SlowAPIMiddleware)

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Device-Token", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    # ── Security headers + request logging ───────────────────────────────────
    app.add_middleware(
        SecurityHeadersMiddleware,
        production=settings.environment == "production",
    )
    app.add_middleware(RequestLoggingMiddleware)

    # ── Routers ───────────────────────────────────────────────────────────────
    prefix = "/api/v1"
    app.include_router(public.router, prefix=prefix, tags=["public"])
    app.include_router(auth.router, prefix=prefix, tags=["auth"])
    app.include_router(dashboard.router, prefix=prefix, tags=["dashboard"])
    app.include_router(admin.router, prefix=prefix, tags=["admin"])

    # ── Error handlers ────────────────────────────────────────────────────────
    @app.exception_handler(404)
    async def not_found(_: Request, exc: Exception) -> JSONResponse:  # noqa: ARG001
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "NOT_FOUND", "message": "Resource not found"}},
        )

    @app.exception_handler(500)
    async def internal_error(_: Request, exc: Exception) -> JSONResponse:  # noqa: ARG001
        logger.error("unhandled_error", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}},
        )

    return app


app = create_app()
