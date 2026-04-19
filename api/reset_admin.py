"""One-off admin password reset. Delete after use."""
import asyncio
from sqlalchemy import select
from app.database.engine import async_session_maker
from app.models.user import User, UserRole
from app.security.password import hash_password


async def main() -> None:
    new_email = "admin@cadence.dev"
    new_password = "admin1234"

    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.role == UserRole.ADMIN)
        )
        admin = result.scalar_one_or_none()
        if not admin:
            print("No admin user found.")
            return

        old_email = admin.email
        admin.email = new_email
        admin.password_hash = hash_password(new_password)
        admin.is_active = True
        await session.commit()

        print(f"✓ Admin updated: {old_email} → {new_email}")
        print(f"✓ Password set to: {new_password}")


if __name__ == "__main__":
    asyncio.run(main())
