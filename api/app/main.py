"""FastAPI application factory and entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database.engine import engine
from app.logging_config import setup_logging
from app.rate_limit import limiter
from app.routers import auth, admin, public, scheduler, webhooks, protocol_api

# Configure logging before anything else
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events."""
    logger.info("Starting %s (env=%s, simulation=%s)", settings.app_name, settings.environment, settings.simulation_mode)

    from app.database.init_db import init_db
    from app.database.seed_db import seed_db
    try:
        await init_db()
        await seed_db()
        logger.info("Database initialization and seeding completed successfully")
    except Exception as e:
        logger.exception("Database initialization failed: %s", e)
        logger.warning("Application will continue, but database may not be ready")

    yield

    logger.info("Shutting down...")
    from app.redis import close_redis
    await close_redis()
    await engine.dispose()


def _init_sentry() -> None:
    """Initialize Sentry error tracking if DSN is configured."""
    if not settings.sentry_dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=0.1 if settings.is_production else 1.0,
            integrations=[FastApiIntegration(), SqlalchemyIntegration()],
            send_default_pii=False,
        )
        logger.info("Sentry initialized (env=%s)", settings.environment)
    except ImportError:
        logger.warning("sentry-sdk not installed, skipping Sentry init")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    _init_sentry()
    enable_docs = settings.debug or not settings.is_production

    app = FastAPI(
        title=settings.app_name,
        description="Messaging Protocol Management System for Health Interventions",
        version="0.1.0",
        docs_url="/docs" if enable_docs else None,
        redoc_url="/redoc" if enable_docs else None,
        lifespan=lifespan,
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(auth.router, prefix="/v1/auth", tags=["Authentication"])
    app.include_router(admin.router, prefix="/v1/admin", tags=["Admin"])
    app.include_router(public.router, prefix="/v1/public", tags=["Public"])
    app.include_router(scheduler.router, prefix="/v1/scheduler", tags=["Scheduler"])
    app.include_router(webhooks.router, prefix="/v1/webhooks", tags=["Webhooks"])
    app.include_router(protocol_api.router, prefix="/v1", tags=["Protocol API"])

    @app.get("/health")
    async def health_check():
        """Liveness probe - confirms the process is running."""
        return {
            "status": "healthy",
            "app": settings.app_name,
            "environment": settings.environment,
        }

    @app.get("/ready")
    async def readiness_check():
        """Readiness probe - confirms DB and Redis are reachable.

        Returns 503 if any dependency is unreachable, signaling
        load balancers to stop routing traffic.
        """
        from fastapi.responses import JSONResponse
        from sqlalchemy import text as sa_text
        from app.database.engine import async_session_maker

        checks: dict[str, str] = {}

        # Database check
        try:
            async with async_session_maker() as session:
                await session.execute(sa_text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as e:
            checks["database"] = f"error: {type(e).__name__}"

        # Redis check
        try:
            from app.redis import get_redis
            redis = await get_redis()
            await redis.ping()
            checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"error: {type(e).__name__}"

        all_ok = all(v == "ok" for v in checks.values())
        status_code = 200 if all_ok else 503

        return JSONResponse(
            status_code=status_code,
            content={
                "status": "ready" if all_ok else "not_ready",
                "checks": checks,
            },
        )

    @app.get("/debug/db")
    async def debug_db():
        """Database connectivity check. Only returns connection status, never data."""
        if settings.is_production:
            return {"status": "disabled_in_production"}

        from sqlalchemy import text
        from app.database.engine import async_session_maker
        async with async_session_maker() as session:
            try:
                await session.execute(text("SELECT 1"))
                return {"status": "connected"}
            except Exception as e:
                return {"status": "error", "error": str(e)}

    return app


app = create_app()
