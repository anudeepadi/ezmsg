"""Authentication dependencies for FastAPI."""

from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.user import User, UserRole
from app.security.jwt import decode_token


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Get the current authenticated user from Bearer header or cookie.

    Checks the Authorization header first (for mobile/API clients),
    then falls back to the 'ezmsg_access' cookie (for web dashboard).

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        User object if authenticated

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = None

    # Check Authorization header first (mobile / API clients)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()

    # Fall back to cookie (web dashboard)
    if not token:
        token = request.cookies.get("ezmsg_access")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_optional_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Get the current user if authenticated, or None if not.

    Unlike get_current_user, this does NOT raise on missing/invalid tokens.
    Used for endpoints that behave differently based on auth status.
    """
    token = None

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()

    if not token:
        token = request.cookies.get("ezmsg_access")

    if not token:
        return None

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    result = await db.execute(select(User).where(User.id == int(user_id)))
    return result.scalar_one_or_none()


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Get the current active user.

    Args:
        user: User from get_current_user dependency

    Returns:
        Active user object

    Raises:
        HTTPException: If user is inactive
    """
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    return user


async def require_admin(
    user: User = Depends(get_current_active_user),
) -> User:
    """Require admin role for the endpoint.

    Args:
        user: Active user from get_current_active_user dependency

    Returns:
        Admin user object

    Raises:
        HTTPException: If user is not an admin
    """
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def require_researcher_or_admin(
    user: User = Depends(get_current_active_user),
) -> User:
    """Require researcher or admin role for the endpoint.

    Args:
        user: Active user from get_current_active_user dependency

    Returns:
        User object with researcher or admin role

    Raises:
        HTTPException: If user doesn't have required role
    """
    if user.role not in [UserRole.ADMIN, UserRole.RESEARCHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Researcher or admin access required",
        )
    return user
