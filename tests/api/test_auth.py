"""Tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_login_success(client: TestClient):
    """Test successful login."""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Ch4ng3M3"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client: TestClient):
    """Test login with invalid password."""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrongpass"}
    )

    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]


def test_login_invalid_username(client: TestClient):
    """Test login with non-existent username."""
    response = client.post(
        "/api/auth/login",
        json={"username": "nonexistent", "password": "password123"}
    )

    assert response.status_code == 401


def test_get_current_user(client: TestClient, admin_token: str):
    """Test getting current user information."""
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"
    assert data["is_active"] is True


def test_get_current_user_no_token(client: TestClient):
    """Test getting current user without token."""
    response = client.get("/api/auth/me")

    assert response.status_code == 403  # No auth header


def test_get_current_user_invalid_token(client: TestClient):
    """Test getting current user with invalid token."""
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )

    assert response.status_code == 401


def test_refresh_token(client: TestClient):
    """Test refreshing access token."""
    # Login first
    login_response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Ch4ng3M3"}
    )
    assert login_response.status_code == 200
    refresh_token = login_response.json()["refresh_token"]

    # Refresh token
    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_token_invalid(client: TestClient):
    """Test refreshing with invalid token."""
    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": "invalid_token"}
    )

    assert response.status_code == 401


def test_logout(client: TestClient, admin_token: str):
    """Test logout endpoint."""
    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    assert "message" in response.json()
