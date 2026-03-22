"""Database seeding script.

This script creates an admin user if one doesn't exist.
Safe to run multiple times - it will skip if admin already exists.
"""

import asyncio
from sqlalchemy import select

from app.database.engine import engine, async_session_maker
from app.models.user import User, UserRole
from app.security.password import hash_password


async def seed_admin_user() -> None:
    """Create default admin user if it doesn't exist."""
    print("Seeding database with admin user...")

    async with async_session_maker() as session:
        # Check if admin user already exists
        result = await session.execute(
            select(User).where(User.email == "admin@example.com")
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print("Admin user already exists. Skipping.")
            return

        # Create admin user
        admin_user = User(
            email="admin@example.com",
            password_hash=hash_password("admin123"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)

        print(f"✅ Created admin user: {admin_user.email} (ID: {admin_user.id})")


async def seed_db() -> None:
    """Seed the database with initial data."""
    try:
        await seed_admin_user()
        print("Database seeding complete!")
    except Exception as e:
        print(f"Error seeding database: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(seed_db())
