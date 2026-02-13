"""Pytest configuration and fixtures for API tests."""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
import httpx
from httpx import ASGITransport

from app.main import app
from app.config import settings


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create an async HTTP client using ASGI transport (in-process)."""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def auth_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create an authenticated client with admin credentials."""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        password = os.getenv("ADMIN_PASSWORD", "admin123")
        response = await client.post(
            "/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert response.status_code == 200, f"Auth failed: {response.text}"
        yield client


@pytest_asyncio.fixture
async def protocol_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create an HTTP client with protocol API key header."""
    transport = ASGITransport(app=app)
    api_key = settings.protocol_api_key
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-API-Key": api_key},
    ) as client:
        yield client
