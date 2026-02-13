"""Tests for public enrollment endpoints."""

import pytest
import httpx


@pytest.mark.asyncio
async def test_enroll_missing_fields(client: httpx.AsyncClient):
    """Enrollment requires project_id."""
    response = await client.post("/v1/public/enroll", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_enroll_nonexistent_project(client: httpx.AsyncClient):
    """Enrollment for non-existent project returns 404."""
    response = await client.post(
        "/v1/public/enroll",
        json={"project_id": 99999},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_participant_status_not_found(client: httpx.AsyncClient):
    """Status for unknown participant UUID returns 404."""
    response = await client.get("/v1/public/participant/nonexistent-uuid/status")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_fcm_token_update_not_found(client: httpx.AsyncClient):
    """FCM token update for unknown participant returns 404."""
    response = await client.post(
        "/v1/public/participant/nonexistent-uuid/fcm-token",
        json={"fcm_token": "fake-token"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_language_update_not_found(client: httpx.AsyncClient):
    """Language update for unknown participant returns 404."""
    response = await client.post(
        "/v1/public/participant/nonexistent-uuid/language",
        json={"language": "es"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_enroll_with_channel_type(client: httpx.AsyncClient):
    """Enrollment accepts channel_type field."""
    response = await client.post(
        "/v1/public/enroll",
        json={"project_id": 99999, "channel_type": "MOBILE_APP"},
    )
    # Should 404 on project, not 422 on channel_type
    assert response.status_code == 404
