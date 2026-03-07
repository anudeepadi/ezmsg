"""Tests for delivery management endpoints."""

import pytest
import httpx


@pytest.mark.asyncio
async def test_channel_status_unauthenticated(client: httpx.AsyncClient):
    """Channel status requires authentication."""
    response = await client.get("/v1/admin/delivery/channel-status")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_channel_status_authenticated(auth_client: httpx.AsyncClient):
    """Channel status returns configuration info."""
    response = await auth_client.get("/v1/admin/delivery/channel-status")
    assert response.status_code == 200
    data = response.json()
    assert "twilio_configured" in data
    assert "fcm_configured" in data
    assert "simulation_mode" in data
    assert isinstance(data["twilio_configured"], bool)
    assert isinstance(data["fcm_configured"], bool)
    assert isinstance(data["simulation_mode"], bool)


@pytest.mark.asyncio
async def test_queue_stats_unauthenticated(client: httpx.AsyncClient):
    """Queue stats requires authentication."""
    response = await client.get("/v1/admin/delivery/project/1/stats")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_queue_stats_authenticated(auth_client: httpx.AsyncClient):
    """Queue stats returns counts per status."""
    response = await auth_client.get("/v1/admin/delivery/project/1/stats")
    assert response.status_code == 200
    data = response.json()
    assert "pending" in data
    assert "sent" in data
    assert "failed" in data
    assert "total" in data
    assert isinstance(data["total"], int)


@pytest.mark.asyncio
async def test_list_messages_unauthenticated(client: httpx.AsyncClient):
    """Message listing requires authentication."""
    response = await client.get("/v1/admin/delivery/project/1/messages")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_messages_authenticated(auth_client: httpx.AsyncClient):
    """Message listing returns paginated results."""
    response = await auth_client.get("/v1/admin/delivery/project/1/messages")
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert isinstance(data["messages"], list)


@pytest.mark.asyncio
async def test_list_messages_invalid_status_filter(auth_client: httpx.AsyncClient):
    """Message listing with invalid status filter returns 400."""
    response = await auth_client.get(
        "/v1/admin/delivery/project/1/messages?status=INVALID"
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_messages_valid_status_filter(auth_client: httpx.AsyncClient):
    """Message listing with valid status filter works."""
    response = await auth_client.get(
        "/v1/admin/delivery/project/1/messages?status=PENDING"
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["messages"], list)


@pytest.mark.asyncio
async def test_test_send_unauthenticated(client: httpx.AsyncClient):
    """Test send requires authentication."""
    response = await client.post(
        "/v1/admin/delivery/test-send",
        json={
            "participant_id": 1,
            "message_text": "Hello test",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_test_send_participant_not_found(auth_client: httpx.AsyncClient):
    """Test send with non-existent participant returns 404."""
    response = await auth_client.post(
        "/v1/admin/delivery/test-send",
        json={
            "participant_id": 999999,
            "message_text": "Hello test",
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_test_send_missing_fields(auth_client: httpx.AsyncClient):
    """Test send with missing required fields returns 422."""
    response = await auth_client.post(
        "/v1/admin/delivery/test-send",
        json={},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_retry_failed_unauthenticated(client: httpx.AsyncClient):
    """Retry failed requires authentication."""
    response = await client.post("/v1/admin/delivery/project/1/retry-failed")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_retry_failed_authenticated(auth_client: httpx.AsyncClient):
    """Retry failed returns count of retried messages."""
    response = await auth_client.post("/v1/admin/delivery/project/1/retry-failed")
    assert response.status_code == 200
    data = response.json()
    assert "retried_count" in data
    assert isinstance(data["retried_count"], int)
