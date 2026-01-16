"""FastAPI application factory and entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.engine import engine
from app.routers import auth, admin, public, scheduler, webhooks


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    print(f"Starting {settings.app_name}...")
    print(f"Environment: {settings.environment}")
    print(f"Simulation mode: {settings.simulation_mode}")

    yield

    # Shutdown
    print("Shutting down...")
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="Messaging Protocol Management System for Health Interventions",
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

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

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "app": settings.app_name,
            "environment": settings.environment,
        }

    return app


app = create_app()
