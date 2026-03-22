"""Tests for scheduler API endpoints."""

import pytest
import httpx


@pytest.mark.asyncio
async def test_scheduler_health_unauthenticated(client: httpx.AsyncClient):
    """Test scheduler health endpoint without authentication."""
    response = await client.get("/v1/scheduler/health")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_scheduler_health_authenticated(auth_client: httpx.AsyncClient):
    """Test scheduler health endpoint with authentication."""
    response = await auth_client.get("/v1/scheduler/health")

    assert response.status_code == 200
    data = response.json()
    assert "pending_count" in data
    assert "in_progress_count" in data
    assert "failed_count" in data
    assert "sent_today" in data


@pytest.mark.asyncio
async def test_scheduler_pending_messages(auth_client: httpx.AsyncClient):
    """Test getting pending messages."""
    response = await auth_client.get("/v1/scheduler/messages/pending")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_scheduler_failed_messages(auth_client: httpx.AsyncClient):
    """Test getting failed messages."""
    response = await auth_client.get("/v1/scheduler/messages/failed")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
