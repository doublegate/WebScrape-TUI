"""Tests for article endpoints."""

from fastapi.testclient import TestClient


def test_list_articles(client: TestClient, auth_headers: dict, sample_article: int):
    """Test listing articles."""
    response = client.get("/api/articles", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "articles" in data
    assert "total" in data
    assert data["total"] >= 1
    assert len(data["articles"]) >= 1


def test_list_articles_pagination(client: TestClient, auth_headers: dict, sample_article: int):
    """Test article pagination."""
    response = client.get(
        "/api/articles?page=1&page_size=1",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 1
    assert len(data["articles"]) <= 1


def test_list_articles_no_auth(client: TestClient):
    """Test listing articles without authentication."""
    response = client.get("/api/articles")

    assert response.status_code == 403


def test_get_article(client: TestClient, auth_headers: dict, sample_article: int):
    """Test getting single article."""
    response = client.get(
        f"/api/articles/{sample_article}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_article
    assert data["title"] == "Test Article"


def test_get_article_not_found(client: TestClient, auth_headers: dict):
    """Test getting non-existent article."""
    response = client.get(
        "/api/articles/99999",
        headers=auth_headers
    )

    assert response.status_code == 404


def test_create_article(client: TestClient, user_auth_headers: dict):
    """Test creating article."""
    response = client.post(
        "/api/articles",
        headers=user_auth_headers,
        json={
            "url": "https://example.com/new",
            "title": "New Article",
            "content": "Article content here",
            "link": "https://example.com/new",
            "tags": ["test", "api"]
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Article"
    assert "test" in data["tags"]


def test_create_article_as_viewer(client: TestClient, viewer_auth_headers: dict):
    """Test that viewer cannot create articles."""
    response = client.post(
        "/api/articles",
        headers=viewer_auth_headers,
        json={
            "url": "https://example.com/new",
            "title": "New Article",
            "content": "Content",
            "link": "https://example.com/new"
        }
    )

    assert response.status_code == 403  # Viewer doesn't have USER role


def test_update_article(client: TestClient, auth_headers: dict, sample_article: int):
    """Test updating article."""
    response = client.put(
        f"/api/articles/{sample_article}",
        headers=auth_headers,
        json={
            "title": "Updated Title",
            "sentiment": "positive"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["sentiment"] == "positive"


def test_update_article_not_owner(client: TestClient, user_auth_headers: dict, sample_article: int):
    """Test that non-owner cannot update article."""
    response = client.put(
        f"/api/articles/{sample_article}",
        headers=user_auth_headers,
        json={"title": "Hacked Title"}
    )

    assert response.status_code == 403  # Not owner


def test_delete_article(client: TestClient, auth_headers: dict, sample_article: int):
    """Test deleting article."""
    response = client.delete(
        f"/api/articles/{sample_article}",
        headers=auth_headers
    )

    assert response.status_code == 204

    # Verify deleted
    get_response = client.get(
        f"/api/articles/{sample_article}",
        headers=auth_headers
    )
    assert get_response.status_code == 404


def test_delete_article_not_owner(client: TestClient, user_auth_headers: dict, sample_article: int):
    """Test that non-owner cannot delete article."""
    response = client.delete(
        f"/api/articles/{sample_article}",
        headers=user_auth_headers
    )

    assert response.status_code == 403  # Not owner
