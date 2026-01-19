"""Pytest configuration and fixtures for API tests."""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
import httpx
from httpx import ASGITransport

from app.main import app


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
        # Login to get cookies
        response = await client.post(
            "/v1/auth/login",
            json={"email": "admin@example.com", "password": "admin123"}
        )
        # Cookies are automatically stored in the client session
        yield client
