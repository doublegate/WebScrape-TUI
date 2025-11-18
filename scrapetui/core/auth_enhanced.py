"""
Enhanced Authentication with Security Features

Integrates password policy, rate limiting, and audit logging
into the authentication system.

Part of v2.2.0 Security Enhancements.
"""

from typing import Optional, Tuple
from datetime import datetime, timezone

from .auth import (
    hash_password,
    verify_password,
    create_session_token,
    db_datetime_now
)
from .password_policy import validate_password, PasswordPolicy
from .rate_limit import get_rate_limiter, LoginAttemptResult
from .audit import log_audit_event, AuditEventType
from .database import get_db_connection


def authenticate_user_enhanced(
    username: str,
    password: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Tuple[Optional[int], Optional[str], str]:
    """
    Authenticate user with enhanced security features.

    Includes rate limiting, audit logging, and account lockout.

    Args:
        username: Username to authenticate
        password: Password to verify
        ip_address: IP address of login attempt
        user_agent: User agent string

    Returns:
        Tuple of (user_id, session_token, message)
        user_id and session_token are None on failure

    Example:
        >>> user_id, token, msg = authenticate_user_enhanced(
        ...     "admin",
        ...     "MyP@ssw0rd123",
        ...     ip_address="127.0.0.1"
        ... )
        >>> if user_id:
        ...     print(f"Login successful: {token}")
        ... else:
        ...     print(f"Login failed: {msg}")
    """
    rate_limiter = get_rate_limiter()

    # Check rate limit first
    rate_check = rate_limiter.check_rate_limit(username)

    if not rate_check.allowed:
        # Log rate limit exceeded
        log_audit_event(
            AuditEventType.RATE_LIMIT_EXCEEDED,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            event_data={'attempts_remaining': 0}
        )
        return None, None, rate_check.message

    # Attempt authentication
    with get_db_connection() as conn:
        conn.row_factory = lambda cursor, row: dict(
            zip([col[0] for col in cursor.description], row)
        )

        user = conn.execute("""
            SELECT id, username, password_hash, is_active, account_locked
            FROM users
            WHERE username = ?
        """, (username,)).fetchone()

        if not user:
            # User doesn't exist - record failed attempt
            rate_limiter.record_login_attempt(
                username,
                success=False,
                ip_address=ip_address
            )

            log_audit_event(
                AuditEventType.LOGIN_FAILURE,
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                event_data={'reason': 'user_not_found'}
            )

            return None, None, "Invalid username or password"

        # Check if account is locked
        if user['account_locked']:
            log_audit_event(
                AuditEventType.UNAUTHORIZED_ACCESS,
                user_id=user['id'],
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                event_data={'reason': 'account_locked'}
            )
            return None, None, "Account is locked. Contact administrator."

        # Check if account is active
        if not user['is_active']:
            log_audit_event(
                AuditEventType.UNAUTHORIZED_ACCESS,
                user_id=user['id'],
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                event_data={'reason': 'account_inactive'}
            )
            return None, None, "Account is inactive"

        # Verify password
        if not verify_password(password, user['password_hash']):
            # Record failed attempt
            rate_limiter.record_login_attempt(
                username,
                success=False,
                ip_address=ip_address
            )

            log_audit_event(
                AuditEventType.LOGIN_FAILURE,
                user_id=user['id'],
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                event_data={'reason': 'invalid_password'}
            )

            return None, None, "Invalid username or password"

        # Successful authentication
        user_id = user['id']

        # Create session
        session_token = create_session_token()
        now = db_datetime_now()
        expires_at = datetime.now(timezone.utc).replace(
            hour=datetime.now(timezone.utc).hour + 24
        ).isoformat()

        conn.execute("""
            INSERT INTO user_sessions
            (session_token, user_id, created_at, expires_at)
            VALUES (?, ?, ?, ?)
        """, (session_token, user_id, now, expires_at))

        # Update last login
        conn.execute("""
            UPDATE users
            SET last_login = ?
            WHERE id = ?
        """, (now, user_id))

        conn.commit()

        # Record successful attempt
        rate_limiter.record_login_attempt(
            username,
            success=True,
            ip_address=ip_address
        )

        # Log successful login
        log_audit_event(
            AuditEventType.LOGIN_SUCCESS,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return user_id, session_token, "Login successful"


def create_user_with_policy(
    username: str,
    password: str,
    email: Optional[str] = None,
    role: str = "user",
    force_password_change: bool = False,
    created_by: Optional[int] = None,
    password_policy: Optional[PasswordPolicy] = None
) -> Tuple[Optional[int], str]:
    """
    Create user with password policy validation.

    Args:
        username: Username for new user
        password: Password (will be validated against policy)
        email: Optional email address
        role: User role (admin, user, viewer)
        force_password_change: Require password change on first login
        created_by: User ID of creator (for audit log)
        password_policy: Custom password policy (uses default if None)

    Returns:
        Tuple of (user_id, message)
        user_id is None on failure

    Example:
        >>> user_id, msg = create_user_with_policy(
        ...     "newuser",
        ...     "Str0ng!P@ssw0rd",
        ...     email="user@example.com",
        ...     role="user"
        ... )
        >>> if user_id:
        ...     print(f"User created: {user_id}")
        ... else:
        ...     print(f"Failed: {msg}")
    """
    # Validate password against policy
    validation = validate_password(password, username, password_policy)

    if not validation.is_valid:
        error_msg = "Password does not meet requirements:\n• " + "\n• ".join(validation.errors)
        return None, error_msg

    # Hash password
    password_hash = hash_password(password)

    # Create user
    now = db_datetime_now()

    try:
        with get_db_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO users
                (username, password_hash, email, role, created_at,
                 is_active, force_password_change, password_changed_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            """, (
                username,
                password_hash,
                email,
                role,
                now,
                1 if force_password_change else 0,
                now
            ))

            user_id = cursor.lastrowid
            conn.commit()

            # Log account creation
            log_audit_event(
                AuditEventType.ACCOUNT_CREATED,
                user_id=user_id,
                username=username,
                event_data={
                    'created_by': created_by,
                    'role': role,
                    'force_password_change': force_password_change
                }
            )

            return user_id, "User created successfully"

    except Exception as e:
        return None, f"Failed to create user: {str(e)}"


def change_password_with_policy(
    user_id: int,
    old_password: str,
    new_password: str,
    password_policy: Optional[PasswordPolicy] = None
) -> Tuple[bool, str]:
    """
    Change user password with policy validation.

    Args:
        user_id: User ID
        old_password: Current password (for verification)
        new_password: New password (will be validated)
        password_policy: Custom password policy (uses default if None)

    Returns:
        Tuple of (success, message)

    Example:
        >>> success, msg = change_password_with_policy(
        ...     user_id=5,
        ...     old_password="OldP@ss123",
        ...     new_password="N3wP@ssw0rd!"
        ... )
        >>> print(msg)
    """
    with get_db_connection() as conn:
        conn.row_factory = lambda cursor, row: dict(
            zip([col[0] for col in cursor.description], row)
        )

        user = conn.execute("""
            SELECT id, username, password_hash
            FROM users
            WHERE id = ?
        """, (user_id,)).fetchone()

        if not user:
            return False, "User not found"

        # Verify old password
        if not verify_password(old_password, user['password_hash']):
            log_audit_event(
                AuditEventType.UNAUTHORIZED_ACCESS,
                user_id=user_id,
                username=user['username'],
                event_data={'reason': 'invalid_old_password'}
            )
            return False, "Current password is incorrect"

        # Validate new password
        validation = validate_password(
            new_password,
            user['username'],
            password_policy
        )

        if not validation.is_valid:
            error_msg = "New password does not meet requirements:\n• " + "\n• ".join(validation.errors)
            return False, error_msg

        # Hash new password
        new_hash = hash_password(new_password)
        now = db_datetime_now()

        # Update password
        conn.execute("""
            UPDATE users
            SET password_hash = ?,
                password_changed_at = ?,
                force_password_change = 0
            WHERE id = ?
        """, (new_hash, now, user_id))

        # Invalidate all sessions (force re-login)
        conn.execute("""
            DELETE FROM user_sessions
            WHERE user_id = ?
        """, (user_id,))

        conn.commit()

        # Log password change
        log_audit_event(
            AuditEventType.PASSWORD_CHANGED,
            user_id=user_id,
            username=user['username']
        )

        return True, "Password changed successfully. Please log in again."


def logout_user(
    session_token: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None
) -> bool:
    """
    Logout user and invalidate session.

    Args:
        session_token: Session token to invalidate
        user_id: Optional user ID for audit log
        username: Optional username for audit log

    Returns:
        True if successful, False otherwise
    """
    with get_db_connection() as conn:
        # Delete session
        conn.execute("""
            DELETE FROM user_sessions
            WHERE session_token = ?
        """, (session_token,))

        conn.commit()

        # Log logout
        if user_id or username:
            log_audit_event(
                AuditEventType.LOGOUT,
                user_id=user_id,
                username=username
            )

        return True
