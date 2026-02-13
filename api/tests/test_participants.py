"""Tests for participant management endpoints."""

import pytest
import httpx


@pytest.mark.asyncio
async def test_list_participants_requires_auth(client: httpx.AsyncClient):
    """Listing participants requires authentication."""
    response = await client.get("/v1/admin/participants/project/1")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_participants_empty_project(auth_client: httpx.AsyncClient):
    """Listing participants for non-existent project returns 404 or empty."""
    response = await auth_client.get("/v1/admin/participants/project/99999")
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_create_participant_requires_auth(client: httpx.AsyncClient):
    """Creating a participant requires authentication."""
    response = await client.post(
        "/v1/admin/participants",
        json={"project_id": 1, "external_id": "TEST001"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_participant_not_found(auth_client: httpx.AsyncClient):
    """Getting a non-existent participant returns 404."""
    response = await auth_client.get("/v1/admin/participants/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_participant_not_found(auth_client: httpx.AsyncClient):
    """Updating a non-existent participant returns 404."""
    response = await auth_client.put(
        "/v1/admin/participants/99999",
        json={"external_id": "UPDATED"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_participant_variables_not_found(auth_client: httpx.AsyncClient):
    """Getting variables for non-existent participant returns 404."""
    response = await auth_client.get("/v1/admin/participants/99999/variables")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_participant_messages_not_found(auth_client: httpx.AsyncClient):
    """Getting messages for non-existent participant returns 404."""
    response = await auth_client.get("/v1/admin/participants/99999/messages")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_bulk_import_requires_auth(client: httpx.AsyncClient):
    """Bulk import requires authentication."""
    response = await client.post(
        "/v1/admin/participants/project/1/import",
        files={"file": ("test.csv", b"external_id\nTEST001", "text/csv")},
    )
    assert response.status_code == 401
