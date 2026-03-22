"""FastAPI application factory and entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.engine import engine
from app.routers import auth, admin, public, scheduler, webhooks, protocol_api


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    print(f"Starting {settings.app_name}...")
    print(f"Environment: {settings.environment}")
    print(f"Simulation mode: {settings.simulation_mode}")
    print(f"Database URL: {settings.database_url[:50]}...")  # Print first 50 chars

    # Initialize database tables
    from app.database.init_db import init_db
    from app.database.seed_db import seed_db
    try:
        await init_db()
        await seed_db()
        print("✅ Database initialization and seeding completed successfully")
    except Exception as e:
        import traceback
        print(f"❌ Database initialization failed:")
        print(f"Error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        print("Application will continue, but database may not be ready")

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
    app.include_router(protocol_api.router, prefix="/v1", tags=["Protocol API"])

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "app": settings.app_name,
            "environment": settings.environment,
        }

    @app.get("/debug/db")
    async def debug_db():
        """Debug endpoint to test database connectivity."""
        from sqlalchemy import text
        from app.database.session import get_db
        from fastapi import Depends
        from sqlalchemy.ext.asyncio import AsyncSession

        async def test_db(db: AsyncSession = Depends(get_db)):
            try:
                # Simple query to test connection
                result = await db.execute(text("SELECT 1 as test"))
                value = result.scalar()

                # Try to count users
                result = await db.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()

                return {
                    "status": "success",
                    "connection": "working",
                    "test_value": value,
                    "user_count": user_count,
                }
            except Exception as e:
                import traceback
                return {
                    "status": "error",
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }

        # Call the dependency manually
        from app.database.engine import async_session_maker
        async with async_session_maker() as session:
            try:
                result = await session.execute(text("SELECT 1 as test"))
                value = result.scalar()

                result = await session.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()

                return {
                    "status": "success",
                    "connection": "working",
                    "test_value": value,
                    "user_count": user_count,
                }
            except Exception as e:
                import traceback
                return {
                    "status": "error",
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }

    return app


app = create_app()
