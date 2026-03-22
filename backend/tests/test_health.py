"""Tests for health check endpoint."""

import pytest
import httpx


@pytest.mark.asyncio
async def test_health_check(client: httpx.AsyncClient):
    """Test that health check endpoint returns healthy status."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "EzMsg API"
    assert "environment" in data


@pytest.mark.asyncio
async def test_health_check_contains_required_fields(client: httpx.AsyncClient):
    """Test health check response contains all required fields."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    required_fields = ["status", "app", "environment"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
