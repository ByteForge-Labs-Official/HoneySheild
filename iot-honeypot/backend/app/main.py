"""
FastAPI application factory.

Wires routers, middleware, OpenTelemetry, Prometheus, and CORS.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import ORJSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1 import api_v1_router
from app.core.config import get_settings
from app.core.logging import CorrelationIdMiddleware, configure_logging
from app.core.logging.config import get_db_handler
from app.db.session import engine
from app.integrations.redis.client import get_redis
from app.services.health import aggregate_health

settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: warm up shared resources, then tear them down."""
    # startup
    await get_redis().ping()
    async with engine.begin() as conn:
        await conn.run_sync(lambda _c: None)  # verify connection
    yield
    # shutdown
    db_handler = get_db_handler()
    if db_handler is not None:
        await db_handler.aclose()
    await engine.dispose()
    await get_redis().aclose()


def create_app() -> FastAPI:
    """Build and return a fully wired FastAPI application."""
    app = FastAPI(
        title="Honeynet Research Platform API",
        version=settings.app_version,
        default_response_class=ORJSONResponse,
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url=None,
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # --- middleware -----------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["*"],
        max_age=600,
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret.get_secret_value(),
        same_site="lax",
        https_only=settings.app_env == "production",
        max_age=8 * 3600,
    )
    # Correlation / trace IDs + http.request.start/end events
    app.add_middleware(CorrelationIdMiddleware)

    # --- routers --------------------------------------------------------
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

    # --- metrics --------------------------------------------------------
    Instrumentator(
        excluded_handlers=["/api/v1/health", "/api/v1/ready"],
        inprogress_name="http_requests_inprogress",
        inprogress_labels=True,
    ).instrument(app).expose(app, endpoint="/api/v1/metrics", include_in_schema=False)

    @app.get("/", include_in_schema=False)
    async def root():
        return {"name": settings.app_name, "version": app.version, "docs": "/docs"}

    return app


app = create_app()
