"""Tests for scraper endpoints."""

from fastapi.testclient import TestClient


def test_list_available_scrapers(client: TestClient, auth_headers: dict):
    """Test listing available scrapers."""
    response = client.get("/api/scrapers/available", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should have at least generic scraper
    assert len(data) >= 1


def test_list_scraper_profiles(client: TestClient, auth_headers: dict):
    """Test listing scraper profiles."""
    response = client.get("/api/scrapers/profiles", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should have preinstalled scrapers
    assert len(data) >= 1


def test_create_scraper_profile(client: TestClient, user_auth_headers: dict):
    """Test creating scraper profile."""
    response = client.post(
        "/api/scrapers/profiles",
        headers=user_auth_headers,
        json={
            "name": "Custom Scraper",
            "url": "https://example.com",
            "selector": ".content",
            "default_limit": 10,
            "description": "Test scraper",
            "is_shared": False
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Custom Scraper"
    assert data["is_shared"] is False


def test_update_scraper_profile(client: TestClient, user_auth_headers: dict):
    """Test updating scraper profile."""
    # Create profile first
    create_response = client.post(
        "/api/scrapers/profiles",
        headers=user_auth_headers,
        json={
            "name": "To Update",
            "url": "https://example.com",
            "selector": ".content",
            "is_shared": False
        }
    )
    profile_id = create_response.json()["id"]

    # Update profile
    response = client.put(
        f"/api/scrapers/profiles/{profile_id}",
        headers=user_auth_headers,
        json={
            "url": "https://updated.com",
            "is_shared": True
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["url"] == "https://updated.com"
    assert data["is_shared"] is True


def test_update_preinstalled_scraper(client: TestClient, auth_headers: dict):
    """Test that preinstalled scrapers cannot be edited."""
    # Get first preinstalled scraper
    profiles_response = client.get(
        "/api/scrapers/profiles",
        headers=auth_headers
    )
    profiles = profiles_response.json()

    preinstalled = [p for p in profiles if p["is_preinstalled"]]
    if preinstalled:
        profile_id = preinstalled[0]["id"]

        response = client.put(
            f"/api/scrapers/profiles/{profile_id}",
            headers=auth_headers,
            json={"url": "https://hacked.com"}
        )

        assert response.status_code == 403  # Cannot edit preinstalled


def test_delete_scraper_profile(client: TestClient, user_auth_headers: dict):
    """Test deleting scraper profile."""
    # Create profile first
    create_response = client.post(
        "/api/scrapers/profiles",
        headers=user_auth_headers,
        json={
            "name": "To Delete",
            "url": "https://example.com",
            "selector": ".content"
        }
    )
    profile_id = create_response.json()["id"]

    # Delete profile
    response = client.delete(
        f"/api/scrapers/profiles/{profile_id}",
        headers=user_auth_headers
    )

    assert response.status_code == 204


def test_delete_preinstalled_scraper(client: TestClient, auth_headers: dict):
    """Test that preinstalled scrapers cannot be deleted."""
    # Get first preinstalled scraper
    profiles_response = client.get(
        "/api/scrapers/profiles",
        headers=auth_headers
    )
    profiles = profiles_response.json()

    preinstalled = [p for p in profiles if p["is_preinstalled"]]
    if preinstalled:
        profile_id = preinstalled[0]["id"]

        response = client.delete(
            f"/api/scrapers/profiles/{profile_id}",
            headers=auth_headers
        )

        assert response.status_code == 403  # Cannot delete preinstalled


def test_scrape_url_generic(client: TestClient, user_auth_headers: dict):
    """Test scraping a URL with generic scraper."""
    # Note: This will try to scrape example.com which may fail
    # In a real test, you'd mock the scraper
    response = client.post(
        "/api/scrapers/scrape",
        headers=user_auth_headers,
        json={
            "url": "https://example.com",
            "scraper_name": "Generic HTML",
            "tags": ["test"]
        }
    )

    # Should at least return a response
    assert response.status_code == 201
    data = response.json()
    assert "success" in data


def test_delete_scraper_not_owner(client: TestClient, user_auth_headers: dict, auth_headers: dict):
    """Test that non-owner cannot delete scraper profile."""
    # Admin creates profile
    create_response = client.post(
        "/api/scrapers/profiles",
        headers=auth_headers,
        json={
            "name": "Admin Scraper",
            "url": "https://example.com",
            "selector": ".content"
        }
    )
    profile_id = create_response.json()["id"]

    # User tries to delete
    response = client.delete(
        f"/api/scrapers/profiles/{profile_id}",
        headers=user_auth_headers
    )

    assert response.status_code == 403  # Not owner
