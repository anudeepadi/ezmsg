"""Database session dependency for FastAPI."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.engine import async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session.

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
