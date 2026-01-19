"""Tests for projects API endpoints."""

import pytest
import httpx


@pytest.mark.asyncio
async def test_list_projects_unauthenticated(client: httpx.AsyncClient):
    """Test listing projects without authentication."""
    response = await client.get("/v1/admin/projects")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_projects_authenticated(auth_client: httpx.AsyncClient):
    """Test listing projects with authentication."""
    response = await auth_client.get("/v1/admin/projects")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_get_project(auth_client: httpx.AsyncClient):
    """Test getting a specific project."""
    # First, list projects to get an ID
    list_response = await auth_client.get("/v1/admin/projects")
    projects = list_response.json()["items"]

    if len(projects) > 0:
        project_id = projects[0]["id"]
        response = await auth_client.get(f"/v1/admin/projects/{project_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert "name" in data
        assert "status" in data


@pytest.mark.asyncio
async def test_get_nonexistent_project(auth_client: httpx.AsyncClient):
    """Test getting a project that doesn't exist."""
    response = await auth_client.get("/v1/admin/projects/99999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_project(auth_client: httpx.AsyncClient):
    """Test creating a new project."""
    response = await auth_client.post(
        "/v1/admin/projects",
        json={
            "name": "Test Project API",
            "description": "A test project for automated testing"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Project API"
    assert data["description"] == "A test project for automated testing"
    assert data["status"] == "DRAFT"


@pytest.mark.asyncio
async def test_create_project_missing_name(auth_client: httpx.AsyncClient):
    """Test creating a project without a name."""
    response = await auth_client.post(
        "/v1/admin/projects",
        json={"description": "No name project"}
    )

    assert response.status_code == 422  # Validation error
