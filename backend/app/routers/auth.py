"""Authentication router - /v1/auth/*."""

from datetime import datetime, timezone
import hashlib

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.session import get_db
from app.models.user import User, RefreshToken, UserRole
from app.security.jwt import create_access_token, create_refresh_token, decode_token
from app.security.password import verify_password, hash_password
from app.security.deps import get_current_active_user

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Registration request schema."""
    email: EmailStr
    password: str
    full_name: str | None = None


class UserResponse(BaseModel):
    """User response schema."""
    id: int
    email: str
    full_name: str | None
    role: str

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Login response schema."""
    message: str
    user: UserResponse


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set authentication cookies on the response."""
    response.set_cookie(
        key="ezmsg_access",
        value=access_token,
        httponly=settings.cookie_httponly,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.access_token_expire_minutes * 60,
        domain=settings.cookie_domain,
    )
    response.set_cookie(
        key="ezmsg_refresh",
        value=refresh_token,
        httponly=settings.cookie_httponly,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        domain=settings.cookie_domain,
    )


def _clear_auth_cookies(response: Response) -> None:
    """Clear authentication cookies from the response."""
    response.delete_cookie(
        key="ezmsg_access",
        domain=settings.cookie_domain,
    )
    response.delete_cookie(
        key="ezmsg_refresh",
        domain=settings.cookie_domain,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Authenticate user and set HttpOnly cookies.

    Args:
        data: Login credentials
        response: FastAPI response for cookie setting
        db: Database session

    Returns:
        Login response with user info

    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Store refresh token hash
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    payload = decode_token(refresh_token)
    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

    db_token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(db_token)

    # Set cookies
    _set_auth_cookies(response, access_token, refresh_token)

    # Return user info
    return LoginResponse(
        message="Login successful",
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
        ),
    )


@router.post("/refresh", status_code=status.HTTP_204_NO_CONTENT)
async def refresh(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Refresh access token using refresh token cookie.

    Args:
        response: FastAPI response for cookie setting
        db: Database session

    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    from fastapi import Request
    from starlette.requests import Request as StarletteRequest

    # Get refresh token from cookie (this is a workaround)
    # In practice, you'd inject Request as a dependency
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh endpoint needs Request injection",
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    """Log out user by clearing auth cookies.

    Args:
        response: FastAPI response for cookie clearing
    """
    _clear_auth_cookies(response)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Get current authenticated user information.

    Args:
        user: Current authenticated user

    Returns:
        User information
    """
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new user (admin only in production).

    Args:
        data: Registration data
        db: Database session

    Returns:
        Created user information

    Raises:
        HTTPException: If email already exists
    """
    # Check if email exists
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=UserRole.OPERATOR,  # Default role
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
    )
