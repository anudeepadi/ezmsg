"""Authentication router - /v1/auth/*."""

from datetime import datetime, timezone
import hashlib

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.rate_limit import limiter

from app.config import settings
from app.database.session import get_db
from app.models.user import User, RefreshToken, UserRole
from app.security.jwt import create_access_token, create_refresh_token, decode_token
from app.security.password import verify_password, hash_password
from app.security.deps import get_current_active_user, get_optional_current_user

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
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "bearer"


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
@limiter.limit("10/minute")
async def login(
    request: Request,
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

    # Set cookies (for web dashboard)
    _set_auth_cookies(response, access_token, refresh_token)

    # Return user info + tokens in body (for mobile / API clients)
    return LoginResponse(
        message="Login successful",
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
        ),
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", status_code=status.HTTP_204_NO_CONTENT)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Refresh access token using refresh token cookie.

    Reads the ezmsg_refresh cookie, validates the refresh token,
    and issues a new access + refresh token pair.

    Args:
        request: FastAPI request (for reading cookies)
        response: FastAPI response (for setting cookies)
        db: Database session

    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    refresh_token = request.cookies.get("ezmsg_refresh")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )

    # Decode and validate the refresh token
    try:
        payload = decode_token(refresh_token)
    except Exception:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Verify refresh token hash exists in DB
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == int(user_id),
        )
    )
    db_token = result.scalar_one_or_none()
    if not db_token:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    # Verify user still exists and is active
    user = await db.get(User, int(user_id))
    if not user or not user.is_active:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
        )

    # Revoke old refresh token
    await db.delete(db_token)

    # Issue new token pair
    new_access = create_access_token(data={"sub": str(user.id)})
    new_refresh = create_refresh_token(data={"sub": str(user.id)})

    # Store new refresh token hash
    new_hash = hashlib.sha256(new_refresh.encode()).hexdigest()
    new_payload = decode_token(new_refresh)
    new_expires = datetime.fromtimestamp(new_payload["exp"], tz=timezone.utc)
    db.add(RefreshToken(user_id=user.id, token_hash=new_hash, expires_at=new_expires))

    _set_auth_cookies(response, new_access, new_refresh)


class RefreshRequest(BaseModel):
    """Refresh request for mobile clients (sends token in body)."""
    refresh_token: str


class RefreshResponse(BaseModel):
    """Refresh response with new token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/refresh/token", response_model=RefreshResponse)
async def refresh_with_token(
    data: RefreshRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> RefreshResponse:
    """Refresh tokens using a refresh token from the request body.

    This endpoint is for mobile/API clients that don't use cookies.
    Web clients should use POST /refresh which reads from cookies.
    """
    try:
        payload = decode_token(data.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Verify refresh token hash exists in DB
    token_hash = hashlib.sha256(data.refresh_token.encode()).hexdigest()
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == int(user_id),
        )
    )
    db_token = result.scalar_one_or_none()
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    # Verify user still exists and is active
    user = await db.get(User, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
        )

    # Revoke old refresh token
    await db.delete(db_token)

    # Issue new token pair
    new_access = create_access_token(data={"sub": str(user.id)})
    new_refresh = create_refresh_token(data={"sub": str(user.id)})

    # Store new refresh token hash
    new_hash = hashlib.sha256(new_refresh.encode()).hexdigest()
    new_payload = decode_token(new_refresh)
    new_expires = datetime.fromtimestamp(new_payload["exp"], tz=timezone.utc)
    db.add(RefreshToken(user_id=user.id, token_hash=new_hash, expires_at=new_expires))

    return RefreshResponse(
        access_token=new_access,
        refresh_token=new_refresh,
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
@limiter.limit("5/minute")
async def register(
    request: Request,
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> UserResponse:
    """Register a new user. Requires admin authentication in production.

    Args:
        data: Registration data
        db: Database session
        current_user: Authenticated user (required in production)

    Returns:
        Created user information

    Raises:
        HTTPException: If email already exists or user lacks permissions
    """
    # In production, only admins can register new users
    if settings.environment == "production":
        if not current_user or current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can register new users",
            )

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
