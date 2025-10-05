"""User management API endpoints (admin only)."""

from typing import List

from fastapi import APIRouter, Depends

from ...core.database import get_db_connection
from ...core.auth import hash_password, change_password, db_datetime_now
from ...models.user import User
from ...utils.logging import get_logger
from ..models import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserPasswordChange,
    UserProfileResponse,
    UserProfileUpdate,
    UserSessionResponse
)
from ..dependencies import get_current_user, require_admin
from ..exceptions import NotFoundException, BadRequestException, ConflictException

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=List[UserResponse])
async def list_users(current_user: User = Depends(require_admin)):
    """
    List all users (admin only).

    Args:
        current_user: Current authenticated user (must be admin)

    Returns:
        List of users
    """
    try:
        with get_db_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM users
                ORDER BY created_at DESC
            """).fetchall()

            users = []
            for row in rows:
                user = User.from_db_row(row)
                users.append(UserResponse(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    role=user.role,
                    created_at=user.created_datetime,
                    last_login=user.last_login_datetime,
                    is_active=user.is_active
                ))

            return users

    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise BadRequestException(detail="Failed to list users")


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_admin)
):
    """
    Get user by ID (admin only).

    Args:
        user_id: User ID
        current_user: Current authenticated user (must be admin)

    Returns:
        User details

    Raises:
        NotFoundException: If user not found
    """
    try:
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()

            if not row:
                raise NotFoundException(detail="User not found")

            user = User.from_db_row(row)

            return UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                role=user.role,
                created_at=user.created_datetime,
                last_login=user.last_login_datetime,
                is_active=user.is_active
            )

    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        raise BadRequestException(detail="Failed to fetch user")


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    user: UserCreate,
    current_user: User = Depends(require_admin)
):
    """
    Create new user (admin only).

    Args:
        user: User data
        current_user: Current authenticated user (must be admin)

    Returns:
        Created user

    Raises:
        ConflictException: If username already exists
    """
    try:
        with get_db_connection() as conn:
            # Check if username exists
            existing = conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (user.username,)
            ).fetchone()

            if existing:
                raise ConflictException(detail="Username already exists")

            # Hash password
            password_hash = hash_password(user.password)

            # Insert user
            cursor = conn.execute("""
                INSERT INTO users (username, password_hash, email, role, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user.username,
                password_hash,
                user.email,
                user.role,
                db_datetime_now()
            ))

            user_id = cursor.lastrowid
            conn.commit()

            logger.info(f"User {user_id} created by admin {current_user.id}")

            # Fetch created user
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()

            created_user = User.from_db_row(row)

            return UserResponse(
                id=created_user.id,
                username=created_user.username,
                email=created_user.email,
                role=created_user.role,
                created_at=created_user.created_datetime,
                last_login=created_user.last_login_datetime,
                is_active=created_user.is_active
            )

    except ConflictException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise BadRequestException(detail="Failed to create user")


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin)
):
    """
    Update user (admin only).

    Args:
        user_id: User ID
        user_update: Updated user data
        current_user: Current authenticated user (must be admin)

    Returns:
        Updated user

    Raises:
        NotFoundException: If user not found
    """
    try:
        with get_db_connection() as conn:
            # Check user exists
            row = conn.execute(
                "SELECT id FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()

            if not row:
                raise NotFoundException(detail="User not found")

            # Build update query
            updates = []
            params = []

            if user_update.email is not None:
                updates.append("email = ?")
                params.append(user_update.email)

            if user_update.role is not None:
                updates.append("role = ?")
                params.append(user_update.role)

            if user_update.is_active is not None:
                updates.append("is_active = ?")
                params.append(1 if user_update.is_active else 0)

            if updates:
                sql = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
                params.append(user_id)
                conn.execute(sql, params)
                conn.commit()

            # Fetch updated user
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()

            logger.info(f"User {user_id} updated by admin {current_user.id}")

            updated_user = User.from_db_row(row)

            return UserResponse(
                id=updated_user.id,
                username=updated_user.username,
                email=updated_user.email,
                role=updated_user.role,
                created_at=updated_user.created_datetime,
                last_login=updated_user.last_login_datetime,
                is_active=updated_user.is_active
            )

    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise BadRequestException(detail="Failed to update user")


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin)
):
    """
    Delete user (admin only).

    Args:
        user_id: User ID
        current_user: Current authenticated user (must be admin)

    Raises:
        NotFoundException: If user not found
        BadRequestException: If trying to delete self
    """
    # Prevent deleting self
    if user_id == current_user.id:
        raise BadRequestException(detail="Cannot delete your own account")

    try:
        with get_db_connection() as conn:
            # Check user exists
            row = conn.execute(
                "SELECT id FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()

            if not row:
                raise NotFoundException(detail="User not found")

            # Delete user (cascade will delete sessions)
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()

            logger.info(f"User {user_id} deleted by admin {current_user.id}")

    except (NotFoundException, BadRequestException):
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise BadRequestException(detail="Failed to delete user")


@router.put("/{user_id}/password", status_code=204)
async def change_user_password(
    user_id: int,
    password_change: UserPasswordChange,
    current_user: User = Depends(get_current_user)
):
    """
    Change user password.

    Args:
        user_id: User ID (must be current user)
        password_change: Old and new passwords
        current_user: Current authenticated user

    Raises:
        ForbiddenException: If trying to change another user's password
        BadRequestException: If old password is incorrect
    """
    # Can only change own password (even admins)
    if user_id != current_user.id:
        from ..exceptions import ForbiddenException
        raise ForbiddenException(detail="Can only change your own password")

    # Use existing change_password function from core.auth
    success = change_password(
        user_id,
        password_change.old_password,
        password_change.new_password
    )

    if not success:
        raise BadRequestException(detail="Old password is incorrect")

    logger.info(f"Password changed for user {user_id}")


# === Sprint 3: Profile and Session Endpoints ===


@router.get("/profile", response_model=UserProfileResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's profile with statistics.

    Args:
        current_user: Current authenticated user

    Returns:
        User profile with article/scraper counts
    """
    try:
        with get_db_connection() as conn:
            # Get article count
            article_count = conn.execute(
                "SELECT COUNT(*) FROM scraped_data WHERE user_id = ?",
                (current_user.id,)
            ).fetchone()[0]

            # Get scraper count
            scraper_count = conn.execute(
                "SELECT COUNT(*) FROM saved_scrapers WHERE user_id = ?",
                (current_user.id,)
            ).fetchone()[0]

            return UserProfileResponse(
                id=current_user.id,
                username=current_user.username,
                email=current_user.email,
                role=current_user.role,
                created_at=current_user.created_datetime,
                last_login=current_user.last_login_datetime,
                is_active=current_user.is_active,
                article_count=article_count,
                scraper_count=scraper_count
            )

    except Exception as e:
        logger.error(f"Error fetching profile for user {current_user.id}: {e}")
        raise BadRequestException(detail="Failed to fetch profile")


@router.put("/profile", response_model=UserProfileResponse)
async def update_current_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update current user's profile (email only).

    Args:
        profile_update: Profile update data
        current_user: Current authenticated user

    Returns:
        Updated profile
    """
    try:
        with get_db_connection() as conn:
            # Update email if provided
            if profile_update.email is not None:
                conn.execute(
                    "UPDATE users SET email = ? WHERE id = ?",
                    (profile_update.email, current_user.id)
                )
                conn.commit()

            # Fetch updated profile
            article_count = conn.execute(
                "SELECT COUNT(*) FROM scraped_data WHERE user_id = ?",
                (current_user.id,)
            ).fetchone()[0]

            scraper_count = conn.execute(
                "SELECT COUNT(*) FROM saved_scrapers WHERE user_id = ?",
                (current_user.id,)
            ).fetchone()[0]

            # Get updated user data
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?",
                (current_user.id,)
            ).fetchone()

            updated_user = User.from_db_row(row)

            logger.info(f"Profile updated for user {current_user.id}")

            return UserProfileResponse(
                id=updated_user.id,
                username=updated_user.username,
                email=updated_user.email,
                role=updated_user.role,
                created_at=updated_user.created_datetime,
                last_login=updated_user.last_login_datetime,
                is_active=updated_user.is_active,
                article_count=article_count,
                scraper_count=scraper_count
            )

    except Exception as e:
        logger.error(f"Error updating profile for user {current_user.id}: {e}")
        raise BadRequestException(detail="Failed to update profile")


@router.get("/sessions", response_model=list[UserSessionResponse])
async def list_user_sessions(current_user: User = Depends(get_current_user)):
    """
    List current user's active sessions.

    Args:
        current_user: Current authenticated user

    Returns:
        List of active sessions
    """
    try:
        # Get current session token from dependencies
        pass

        # We need the request to get the current session token
        # For now, we'll mark all sessions as not current and let the client determine
        # In a real implementation, we'd pass the current session token

        with get_db_connection() as conn:
            rows = conn.execute("""
                SELECT id, created_at, expires_at
                FROM user_sessions
                WHERE user_id = ?
                AND datetime(expires_at) > datetime('now')
                ORDER BY created_at DESC
            """, (current_user.id,)).fetchall()

            sessions = []
            for row in rows:
                sessions.append(UserSessionResponse(
                    id=row[0],
                    created_at=row[1],
                    expires_at=row[2],
                    is_current=False  # TODO: Compare with current session token
                ))

            logger.info(f"Listed {len(sessions)} active sessions for user {current_user.id}")

            return sessions

    except Exception as e:
        logger.error(f"Error listing sessions for user {current_user.id}: {e}")
        raise BadRequestException(detail="Failed to list sessions")


@router.delete("/sessions/{session_id}", status_code=204)
async def revoke_user_session(
    session_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Revoke a user session.

    Args:
        session_id: Session ID to revoke
        current_user: Current authenticated user

    Raises:
        NotFoundException: If session not found
        ForbiddenException: If session belongs to another user
    """
    try:
        with get_db_connection() as conn:
            # Check session exists and belongs to user
            row = conn.execute(
                "SELECT user_id FROM user_sessions WHERE id = ?",
                (session_id,)
            ).fetchone()

            if not row:
                raise NotFoundException(detail="Session not found")

            if row[0] != current_user.id:
                from ..exceptions import ForbiddenException
                raise ForbiddenException(detail="Cannot revoke another user's session")

            # Delete session
            conn.execute("DELETE FROM user_sessions WHERE id = ?", (session_id,))
            conn.commit()

            logger.info(f"Session {session_id} revoked by user {current_user.id}")

    except (NotFoundException, BadRequestException):
        raise
    except Exception as e:
        logger.error(f"Error revoking session {session_id}: {e}")
        raise BadRequestException(detail="Failed to revoke session")
