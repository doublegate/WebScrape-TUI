"""Authentication and password management for WebScrape-TUI."""

import bcrypt
import secrets
from typing import Optional
from datetime import datetime, timedelta

from .database import get_db_connection
from ..utils.logging import get_logger
from ..utils.errors import AuthenticationError, DatabaseError
from ..constants import DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD

logger = get_logger(__name__)


def db_datetime_now() -> str:
    """Get current datetime as ISO string for database storage."""
    return datetime.now().isoformat()


def db_datetime_future(hours: int = 24) -> str:
    """Get future datetime as ISO string for database storage."""
    return (datetime.now() + timedelta(hours=hours)).isoformat()


def parse_db_datetime(iso_string: Optional[str]) -> Optional[datetime]:
    """Parse ISO datetime string from database to datetime object."""
    return datetime.fromisoformat(iso_string) if iso_string else None


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt with cost factor 12.

    Args:
        password: Plaintext password to hash

    Returns:
        Bcrypt hash string
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify password against bcrypt hash.

    Args:
        password: Plaintext password to verify
        password_hash: Bcrypt hash to check against

    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def create_session_token() -> str:
    """
    Generate cryptographically secure session token (32 bytes).

    Returns:
        URL-safe base64-encoded token string
    """
    return secrets.token_urlsafe(32)


def create_user_session(
    user_id: int,
    duration_hours: int = 24,
    ip_address: Optional[str] = None
) -> str:
    """
    Create new session for user.

    Args:
        user_id: User ID to create session for
        duration_hours: Session validity duration (default 24 hours)
        ip_address: Optional IP address to associate with session

    Returns:
        Session token string
    """
    with get_db_connection() as conn:
        token = create_session_token()
        expires_at = db_datetime_future(duration_hours)

        conn.execute("""
            INSERT INTO user_sessions (user_id, session_token, expires_at, ip_address)
            VALUES (?, ?, ?, ?)
        """, (user_id, token, expires_at, ip_address))
        conn.commit()

        logger.info(f"Created session for user_id={user_id}, expires at {expires_at}")
        return token


def validate_session(session_token: str) -> Optional[int]:
    """
    Validate session token and return user_id if valid.

    Args:
        session_token: Session token to validate

    Returns:
        user_id if session is valid and not expired, None otherwise
    """
    if not session_token:
        return None

    try:
        with get_db_connection() as conn:
            row = conn.execute("""
                SELECT user_id, expires_at
                FROM user_sessions
                WHERE session_token = ? AND expires_at > ?
            """, (session_token, db_datetime_now())).fetchone()

            if row:
                logger.debug(f"Session validated for user_id={row['user_id']}")
                return row['user_id']
            else:
                logger.debug("Session invalid or expired")
                return None
    except Exception as e:
        logger.error(f"Session validation error: {e}", exc_info=True)
        return None


def logout_session(session_token: str) -> None:
    """
    Delete session from database.

    Args:
        session_token: Session token to logout
    """
    try:
        with get_db_connection() as conn:
            conn.execute(
                "DELETE FROM user_sessions WHERE session_token = ?",
                (session_token,)
            )
            conn.commit()
            logger.info("Session logged out successfully")
    except Exception as e:
        logger.error(f"Session logout error: {e}", exc_info=True)


def authenticate_user(username: str, password: str) -> Optional[int]:
    """
    Authenticate user with username and password.

    Args:
        username: Username to authenticate
        password: Plaintext password to verify

    Returns:
        user_id if credentials are valid and user is active, None otherwise
    """
    try:
        with get_db_connection() as conn:
            row = conn.execute("""
                SELECT id, password_hash, is_active
                FROM users
                WHERE username = ?
            """, (username,)).fetchone()

            if row and row['is_active'] and verify_password(
                password, row['password_hash']
            ):
                # Update last_login timestamp
                conn.execute(
                    "UPDATE users SET last_login = ? WHERE id = ?",
                    (db_datetime_now(), row['id'])
                )
                conn.commit()
                logger.info(f"User authenticated: {username}")
                return row['id']
            else:
                logger.warning(f"Authentication failed for username: {username}")
                return None
    except Exception as e:
        logger.error(f"Authentication error: {e}", exc_info=True)
        return None


def change_password(user_id: int, old_password: str, new_password: str) -> bool:
    """
    Change user password.

    Args:
        user_id: User ID
        old_password: Current password for verification
        new_password: New password to set

    Returns:
        True if password changed successfully, False otherwise
    """
    try:
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT password_hash FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()

            if not row:
                logger.error(f"User not found: {user_id}")
                return False

            if not verify_password(old_password, row['password_hash']):
                logger.warning(f"Old password verification failed for user_id={user_id}")
                return False

            new_hash = hash_password(new_password)
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (new_hash, user_id)
            )
            conn.commit()
            logger.info(f"Password changed for user_id={user_id}")
            return True
    except Exception as e:
        logger.error(f"Password change error: {e}", exc_info=True)
        return False


def initialize_admin_user() -> None:
    """
    Create default admin user on first run if no users exist.
    Uses configuration: username='admin', password='Ch4ng3M3'
    """
    try:
        with get_db_connection() as conn:
            # Check if any users exist
            count_row = conn.execute(
                "SELECT COUNT(*) as cnt FROM users"
            ).fetchone()

            if count_row['cnt'] == 0:
                # Create default admin user
                password_hash = hash_password(DEFAULT_ADMIN_PASSWORD)
                conn.execute("""
                    INSERT INTO users (username, password_hash, email, role, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    DEFAULT_ADMIN_USERNAME,
                    password_hash,
                    'admin@localhost',
                    'admin',
                    db_datetime_now()
                ))
                conn.commit()
                logger.info(
                    f"Default admin user created: username='{DEFAULT_ADMIN_USERNAME}', "
                    f"password='{DEFAULT_ADMIN_PASSWORD}' (please change after first login)"
                )
    except Exception as e:
        logger.error(f"Admin user initialization error: {e}", exc_info=True)


def cleanup_expired_sessions() -> int:
    """
    Remove expired sessions from database.

    Returns:
        Number of sessions cleaned up
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM user_sessions
                WHERE expires_at < ?
            """, (db_datetime_now(),))
            conn.commit()
            count = cursor.rowcount
            if count > 0:
                logger.info(f"Cleaned up {count} expired sessions")
            return count
    except Exception as e:
        logger.error(f"Session cleanup error: {e}", exc_info=True)
        return 0
