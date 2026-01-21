"""Database initialization script.

This script creates all tables in the database on startup.
It's safe to run multiple times - it will only create missing tables.
"""

import asyncio
from sqlalchemy import inspect, text

from app.database.engine import engine
from app.models import Base


async def init_db() -> None:
    """Initialize database by creating all tables."""
    print("Initializing database...")

    async with engine.begin() as conn:
        # Check what tables exist
        def check_tables(connection):
            inspector = inspect(connection)
            existing_tables = inspector.get_table_names()
            return existing_tables

        existing_tables = await conn.run_sync(check_tables)
        print(f"Existing tables: {existing_tables}")

        # Create enum type if it doesn't exist
        print("Creating enum types...")
        await conn.execute(
            text("""
                DO $$ BEGIN
                    CREATE TYPE user_role AS ENUM ('admin', 'researcher', 'operator');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """)
        )

        # Create all tables defined in models
        print("Creating missing tables...")
        await conn.run_sync(Base.metadata.create_all)

        # Check tables again
        new_tables = await conn.run_sync(check_tables)
        print(f"Tables after initialization: {new_tables}")

    print("Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(init_db())
