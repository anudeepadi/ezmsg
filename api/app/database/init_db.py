"""Database initialization script.

This script creates all tables in the database on startup.
It's safe to run multiple times - it will only create missing tables.
"""

import asyncio
import os
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

        # Check if enum type exists
        result = await conn.execute(
            text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role')")
        )
        enum_exists = result.scalar()
        print(f"Enum type 'user_role' exists: {enum_exists}")

        reset_db = os.getenv("EZMSG_RESET_DB", "false").strip().lower() in {"1", "true", "yes"}

        if reset_db and existing_tables:
            print("EZMSG_RESET_DB=true: dropping all tables (CASCADE) for a clean initialization...")
            for table in existing_tables:
                try:
                    await conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
                except Exception as e:
                    print(f"Warning: Could not drop table {table}: {e}")

            print("Dropping enum type user_role (CASCADE)...")
            await conn.execute(text("DROP TYPE IF EXISTS user_role CASCADE"))
            enum_exists = False

        # Ensure enum type exists (models use create_type=False)
        if not enum_exists:
            print("Creating enum type user_role...")
            await conn.execute(
                text("CREATE TYPE user_role AS ENUM ('admin', 'researcher', 'operator')")
            )

        # Create all tables defined in models
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)

        # Check tables again
        new_tables = await conn.run_sync(check_tables)
        print(f"Tables after initialization: {new_tables}")

    print("Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(init_db())
