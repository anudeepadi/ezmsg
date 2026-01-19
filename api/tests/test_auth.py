"""Tests for authentication endpoints."""

import pytest
import httpx


@pytest.mark.asyncio
async def test_login_success(client: httpx.AsyncClient):
    """Test successful login with valid credentials."""
    response = await client.post(
        "/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login successful"
    assert "user" in data
    assert data["user"]["email"] == "admin@example.com"
    assert data["user"]["role"] == "admin"


@pytest.mark.asyncio
async def test_login_invalid_email(client: httpx.AsyncClient):
    """Test login with invalid email."""
    response = await client.post(
        "/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "password123"}
    )

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_login_invalid_password(client: httpx.AsyncClient):
    """Test login with invalid password."""
    response = await client.post(
        "/v1/auth/login",
        json={"email": "admin@example.com", "password": "wrongpassword"}
    )

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_login_missing_fields(client: httpx.AsyncClient):
    """Test login with missing required fields."""
    response = await client.post(
        "/v1/auth/login",
        json={"email": "admin@example.com"}
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_login_invalid_email_format(client: httpx.AsyncClient):
    """Test login with invalid email format."""
    response = await client.post(
        "/v1/auth/login",
        json={"email": "not-an-email", "password": "password123"}
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_me_unauthenticated(client: httpx.AsyncClient):
    """Test /me endpoint without authentication."""
    response = await client.get("/v1/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(auth_client: httpx.AsyncClient):
    """Test /me endpoint with authentication."""
    response = await auth_client.get("/v1/auth/me")

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@example.com"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_logout(auth_client: httpx.AsyncClient):
    """Test logout endpoint."""
    response = await auth_client.post("/v1/auth/logout")

    # Logout returns 204 No Content on success
    assert response.status_code in [200, 204]
