"""Database reset script - drops and recreates all tables.

WARNING: This will delete all data!
Only use in development or when database schema needs to be reset.
"""

import asyncio
from sqlalchemy import text

from app.database.engine import engine
from app.models import Base


async def reset_db() -> None:
    """Drop all tables and recreate them."""
    print("WARNING: Resetting database - this will delete all data!")

    async with engine.begin() as conn:
        # Drop all tables
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)

        # Create enum type
        print("Creating enum types...")
        await conn.execute(
            text("""
                DROP TYPE IF EXISTS user_role CASCADE;
                CREATE TYPE user_role AS ENUM ('admin', 'researcher', 'operator');
            """)
        )

        # Recreate all tables
        print("Recreating all tables...")
        await conn.run_sync(Base.metadata.create_all)

    print("Database reset complete!")


if __name__ == "__main__":
    asyncio.run(reset_db())
