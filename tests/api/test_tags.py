"""Tests for tag endpoints."""

from fastapi.testclient import TestClient


def test_list_tags(client: TestClient, auth_headers: dict):
    """Test listing tags."""
    response = client.get("/api/tags", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_create_tag(client: TestClient, user_auth_headers: dict):
    """Test creating tag."""
    response = client.post(
        "/api/tags",
        headers=user_auth_headers,
        json={"name": "newtag"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "newtag"
    assert data["article_count"] == 0


def test_create_tag_duplicate(client: TestClient, user_auth_headers: dict):
    """Test creating duplicate tag."""
    # Create first tag
    client.post(
        "/api/tags",
        headers=user_auth_headers,
        json={"name": "duplicate"}
    )

    # Try to create duplicate
    response = client.post(
        "/api/tags",
        headers=user_auth_headers,
        json={"name": "duplicate"}
    )

    assert response.status_code == 409  # Conflict


def test_delete_tag(client: TestClient, user_auth_headers: dict):
    """Test deleting tag."""
    # Create tag
    create_response = client.post(
        "/api/tags",
        headers=user_auth_headers,
        json={"name": "todelete"}
    )
    tag_id = create_response.json()["id"]

    # Delete tag
    response = client.delete(
        f"/api/tags/{tag_id}",
        headers=user_auth_headers
    )

    assert response.status_code == 204


def test_delete_tag_not_found(client: TestClient, user_auth_headers: dict):
    """Test deleting non-existent tag."""
    response = client.delete(
        "/api/tags/99999",
        headers=user_auth_headers
    )

    assert response.status_code == 404


def test_get_articles_by_tag(client: TestClient, auth_headers: dict):
    """Test getting articles by tag."""
    # Create tag
    tag_response = client.post(
        "/api/tags",
        headers=auth_headers,
        json={"name": "testtag"}
    )
    tag_id = tag_response.json()["id"]

    # Get articles (should be empty)
    response = client.get(
        f"/api/tags/{tag_id}/articles",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0  # No articles with this tag yet
