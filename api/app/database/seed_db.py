"""Database seeding script.

Creates an admin user on first run using credentials from environment variables.
Skips if an admin already exists. Never ships with hardcoded passwords.
"""

import asyncio
import logging
import secrets

from sqlalchemy import select

from app.config import settings
from app.database.engine import async_session_maker
from app.models.user import User, UserRole
from app.security.password import hash_password

logger = logging.getLogger(__name__)


async def seed_admin_user() -> None:
    """Create default admin user if none exists."""
    logger.info("Checking for existing admin user...")

    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.role == UserRole.ADMIN)
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            logger.info("Admin user already exists: %s", existing_admin.email)
            return

        # Determine credentials from env vars or generate a one-time password
        email = settings.admin_email
        password = settings.admin_password

        if not password:
            if settings.is_production:
                logger.warning(
                    "ADMIN_PASSWORD not set in production. "
                    "Skipping admin seed. Create an admin via the register endpoint."
                )
                return
            # Development: generate a random password and log it once
            password = secrets.token_urlsafe(16)
            logger.warning("Generated admin password (save this): %s", password)

        admin_user = User(
            email=email,
            password_hash=hash_password(password),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)

        logger.info("Created admin user: %s (ID: %d)", admin_user.email, admin_user.id)


async def seed_db() -> None:
    """Seed the database with initial data."""
    try:
        await seed_admin_user()
        logger.info("Database seeding complete")
    except Exception as e:
        logger.exception("Error seeding database: %s", e)
        raise


if __name__ == "__main__":
    asyncio.run(seed_db())
