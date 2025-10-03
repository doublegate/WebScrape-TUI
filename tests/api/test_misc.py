"""Tests for miscellaneous API endpoints (root, health, rate limiting)."""

import pytest
from fastapi.testclient import TestClient
import time


def test_root_endpoint(client: TestClient):
    """Test root endpoint."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "WebScrape-TUI" in data["name"]


def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_api_docs_accessible(client: TestClient):
    """Test that API docs are accessible."""
    response = client.get("/api/docs")

    assert response.status_code == 200
    # Docs should return HTML
    assert "text/html" in response.headers.get("content-type", "")


def test_openapi_spec(client: TestClient):
    """Test OpenAPI spec is available."""
    response = client.get("/api/openapi.json")

    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert data["info"]["title"] == "WebScrape-TUI API"


def test_rate_limiting_headers(client: TestClient, auth_headers: dict):
    """Test that rate limiting headers are present."""
    response = client.get("/api/articles", headers=auth_headers)

    assert response.status_code == 200
    # Check for rate limit headers
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers


def test_request_logging_headers(client: TestClient, auth_headers: dict):
    """Test that request logging adds timing header."""
    response = client.get("/api/articles", headers=auth_headers)

    assert response.status_code == 200
    # Check for process time header
    assert "X-Process-Time" in response.headers
    process_time = float(response.headers["X-Process-Time"])
    assert process_time >= 0


def test_cors_headers(client: TestClient):
    """Test CORS headers are present."""
    response = client.get("/")

    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers.keys()


def test_auth_required_endpoints(client: TestClient):
    """Test that protected endpoints require authentication."""
    endpoints = [
        "/api/articles",
        "/api/scrapers/available",
        "/api/tags",
        "/api/users"
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 403, f"Endpoint {endpoint} should require auth"


def test_admin_only_endpoints(client: TestClient, user_auth_headers: dict):
    """Test that admin-only endpoints reject regular users."""
    response = client.get("/api/users", headers=user_auth_headers)

    assert response.status_code == 403  # Non-admin forbidden


def test_invalid_method(client: TestClient, auth_headers: dict):
    """Test invalid HTTP method on endpoint."""
    # Try PATCH on endpoint that doesn't support it
    response = client.patch("/api/tags", headers=auth_headers)

    assert response.status_code == 405  # Method not allowed


def test_malformed_json(client: TestClient, user_auth_headers: dict):
    """Test handling of malformed JSON."""
    response = client.post(
        "/api/tags",
        headers={
            **user_auth_headers,
            "Content-Type": "application/json"
        },
        data="{invalid json}"
    )

    assert response.status_code == 422  # Unprocessable entity
