"""Tests for user management endpoints."""

from fastapi.testclient import TestClient


def test_list_users_as_admin(client: TestClient, auth_headers: dict):
    """Test listing users as admin."""
    response = client.get("/api/users", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # At least admin user


def test_list_users_as_non_admin(client: TestClient, user_auth_headers: dict):
    """Test that non-admin cannot list users."""
    response = client.get("/api/users", headers=user_auth_headers)

    assert response.status_code == 403


def test_create_user_as_admin(client: TestClient, auth_headers: dict):
    """Test creating user as admin."""
    response = client.post(
        "/api/users",
        headers=auth_headers,
        json={
            "username": "newuser",
            "password": "password123",
            "email": "new@example.com",
            "role": "user"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["role"] == "user"


def test_create_user_duplicate_username(client: TestClient, auth_headers: dict):
    """Test creating user with duplicate username."""
    response = client.post(
        "/api/users",
        headers=auth_headers,
        json={
            "username": "admin",  # Duplicate
            "password": "password123",
            "email": "test@example.com",
            "role": "user"
        }
    )

    assert response.status_code == 409  # Conflict


def test_update_user(client: TestClient, auth_headers: dict, user_token: str):
    """Test updating user."""
    # Get user ID
    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    user_id = me_response.json()["id"]

    # Update user
    response = client.put(
        f"/api/users/{user_id}",
        headers=auth_headers,
        json={
            "email": "updated@example.com",
            "role": "admin"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "updated@example.com"
    assert data["role"] == "admin"


def test_delete_user(client: TestClient, auth_headers: dict, user_token: str):
    """Test deleting user."""
    # Get user ID
    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    user_id = me_response.json()["id"]

    # Delete user
    response = client.delete(
        f"/api/users/{user_id}",
        headers=auth_headers
    )

    assert response.status_code == 204


def test_delete_self(client: TestClient, admin_token: str):
    """Test that admin cannot delete own account."""
    # Get admin ID
    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    admin_id = me_response.json()["id"]

    # Try to delete self
    response = client.delete(
        f"/api/users/{admin_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 400  # Cannot delete self


def test_change_password(client: TestClient, user_token: str):
    """Test changing password."""
    # Get user ID
    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    user_id = me_response.json()["id"]

    # Change password
    response = client.put(
        f"/api/users/{user_id}/password",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "old_password": "testpass123",
            "new_password": "newpass456"
        }
    )

    assert response.status_code == 204

    # Verify new password works
    login_response = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "newpass456"}
    )
    assert login_response.status_code == 200


def test_change_password_wrong_old(client: TestClient, user_token: str):
    """Test changing password with wrong old password."""
    # Get user ID
    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    user_id = me_response.json()["id"]

    # Try to change with wrong old password
    response = client.put(
        f"/api/users/{user_id}/password",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "old_password": "wrongpass",
            "new_password": "newpass456"
        }
    )

    assert response.status_code == 400  # Bad request
