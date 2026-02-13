"""Tests for the Protocol API endpoints."""

import pytest
import httpx


@pytest.mark.asyncio
async def test_protocol_start_requires_api_key(client: httpx.AsyncClient):
    """Protocol start requires X-API-Key header."""
    response = await client.post(
        "/v1/protocol/start",
        json={"project_id": 1, "language": "en"},
    )
    assert response.status_code == 422  # Missing required header


@pytest.mark.asyncio
async def test_protocol_start_invalid_api_key(client: httpx.AsyncClient):
    """Protocol start rejects invalid API key."""
    response = await client.post(
        "/v1/protocol/start",
        json={"project_id": 1, "language": "en"},
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protocol_start_missing_project(protocol_client: httpx.AsyncClient):
    """Protocol start with non-existent project returns 404."""
    response = await protocol_client.post(
        "/v1/protocol/start",
        json={"project_id": 99999, "language": "en"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_protocol_start_missing_body(protocol_client: httpx.AsyncClient):
    """Protocol start without body returns 422."""
    response = await protocol_client.post("/v1/protocol/start")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_protocol_respond_invalid_session(protocol_client: httpx.AsyncClient):
    """Protocol respond with fake session ID returns 404."""
    response = await protocol_client.post(
        "/v1/protocol/respond",
        json={"session_id": "nonexistent-session-id", "response": "1"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_protocol_session_status_not_found(protocol_client: httpx.AsyncClient):
    """Session status for nonexistent session returns 404."""
    response = await protocol_client.get("/v1/protocol/session/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_protocol_session_delete_not_found(protocol_client: httpx.AsyncClient):
    """Deleting nonexistent session returns 404."""
    response = await protocol_client.delete("/v1/protocol/session/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_protocol_resume_missing_participant(protocol_client: httpx.AsyncClient):
    """Resume with non-existent participant returns 404."""
    response = await protocol_client.post(
        "/v1/protocol/resume",
        json={"participant_uuid": "nonexistent-uuid"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_protocol_resume_missing_body(protocol_client: httpx.AsyncClient):
    """Resume without body returns 422."""
    response = await protocol_client.post("/v1/protocol/resume")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_protocol_respond_missing_fields(protocol_client: httpx.AsyncClient):
    """Protocol respond without required fields returns 422."""
    response = await protocol_client.post(
        "/v1/protocol/respond",
        json={"session_id": "some-id"},  # Missing 'response' field
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_protocol_start_invalid_language(protocol_client: httpx.AsyncClient):
    """Protocol start accepts any language string (no validation constraint)."""
    response = await protocol_client.post(
        "/v1/protocol/start",
        json={"project_id": 99999, "language": "xx"},
    )
    # Should still hit 404 (project not found), not 422
    assert response.status_code == 404
