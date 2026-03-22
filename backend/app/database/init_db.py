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

        # Check if enum type exists
        result = await conn.execute(
            text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role')")
        )
        enum_exists = result.scalar()
        print(f"Enum type 'user_role' exists: {enum_exists}")

        # If enum doesn't exist but tables do, we need to recreate everything
        if not enum_exists and existing_tables:
            print("Enum type missing but tables exist - dropping all tables...")
            await conn.run_sync(Base.metadata.drop_all)
            existing_tables = []

        # Create enum type if needed (values must match UserRole enum names)
        if not enum_exists:
            print("Creating enum types...")
            await conn.execute(
                text("CREATE TYPE user_role AS ENUM ('ADMIN', 'RESEARCHER', 'OPERATOR')")
            )
        else:
            print("Enum types already exist, skipping.")

        # Create all tables defined in models
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)

        # Check tables again
        new_tables = await conn.run_sync(check_tables)
        print(f"Tables after initialization: {new_tables}")

    print("Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(init_db())
