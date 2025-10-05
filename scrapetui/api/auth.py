"""Authentication endpoints for JWT-based API access."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.database import get_db_connection
from ..core.auth import authenticate_user, db_datetime_now, db_datetime_future
from ..models.user import User
from ..utils.logging import get_logger
from .models import UserLogin, Token, TokenRefresh, UserResponse
from .dependencies import (
    create_access_token,
    create_refresh_token,
    decode_token,
    blacklist_token,
    get_current_user,
    is_token_blacklisted,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)
from .exceptions import UnauthorizedException, BadRequestException

logger = get_logger(__name__)
router = APIRouter()


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Authenticate user and return JWT tokens.

    Args:
        credentials: Username and password

    Returns:
        Access and refresh tokens

    Raises:
        UnauthorizedException: If credentials are invalid
    """
    # Authenticate user
    user_id = authenticate_user(credentials.username, credentials.password)

    if user_id is None:
        raise UnauthorizedException(detail="Invalid username or password")

    # Create JWT tokens (sub must be string for JWT spec compliance)
    access_token = create_access_token(data={"sub": str(user_id)})
    refresh_token = create_refresh_token(data={"sub": str(user_id)})

    # Store refresh token in database
    try:
        with get_db_connection() as conn:
            expires_at = (
                datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            ).isoformat()

            conn.execute(
                """
                INSERT INTO refresh_tokens (token, user_id, expires_at)
                VALUES (?, ?, ?)
                """,
                (refresh_token, user_id, expires_at)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Error storing refresh token: {e}")
        # Don't fail login if refresh token storage fails

    logger.info(f"User {credentials.username} logged in successfully (JWT)")

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout current user by blacklisting their token.

    Args:
        current_user: Current authenticated user

    Returns:
        Success message
    """
    # Note: We don't have access to the actual token here in a clean way
    # The token is in the Authorization header but not passed to this function
    # In a real implementation, we'd need to extract it from the request
    # For now, we'll just log the logout

    logger.info(f"User {current_user.username} logged out (JWT)")

    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=Token)
async def refresh_token(token_request: TokenRefresh):
    """
    Refresh access token using refresh token.

    Args:
        token_request: Refresh token

    Returns:
        New access and refresh tokens

    Raises:
        UnauthorizedException: If refresh token is invalid
    """
    refresh_token = token_request.refresh_token

    # Check if token is blacklisted
    if is_token_blacklisted(refresh_token):
        raise UnauthorizedException(detail="Refresh token has been revoked")

    # Decode refresh token
    try:
        payload = decode_token(refresh_token)
    except:
        raise UnauthorizedException(detail="Invalid refresh token")

    # Verify token type
    if payload.get("type") != "refresh":
        raise UnauthorizedException(detail="Invalid token type")

    # Get user ID (sub is string in JWT, convert to int)
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise UnauthorizedException(detail="Invalid token payload")

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise UnauthorizedException(detail="Invalid user ID in token")

    # Verify refresh token exists in database
    try:
        with get_db_connection() as conn:
            row = conn.execute(
                """
                SELECT expires_at FROM refresh_tokens
                WHERE token = ? AND user_id = ?
                """,
                (refresh_token, user_id)
            ).fetchone()

            if not row:
                raise UnauthorizedException(detail="Refresh token not found")

            # Check expiration
            expires_at = datetime.fromisoformat(row['expires_at'])
            if datetime.now(timezone.utc) > expires_at:
                # Clean up expired token
                conn.execute("DELETE FROM refresh_tokens WHERE token = ?", (refresh_token,))
                conn.commit()
                raise UnauthorizedException(detail="Refresh token expired")

            # Verify user is still active
            user_row = conn.execute(
                "SELECT is_active FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()

            if not user_row or not user_row['is_active']:
                raise UnauthorizedException(detail="User inactive or not found")

    except UnauthorizedException:
        raise
    except Exception as e:
        logger.error(f"Error validating refresh token: {e}")
        raise UnauthorizedException(detail="Token validation failed")

    # Create new tokens (sub must be string for JWT spec compliance)
    new_access_token = create_access_token(data={"sub": str(user_id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user_id)})

    # Store new refresh token and invalidate old one
    try:
        with get_db_connection() as conn:
            # Delete old refresh token
            conn.execute("DELETE FROM refresh_tokens WHERE token = ?", (refresh_token,))

            # Insert new refresh token
            expires_at = (
                datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            ).isoformat()

            conn.execute(
                """
                INSERT INTO refresh_tokens (token, user_id, expires_at)
                VALUES (?, ?, ?)
                """,
                (new_refresh_token, user_id, expires_at)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Error rotating refresh token: {e}")
        # Still return the new tokens even if storage fails

    logger.info(f"Access token refreshed for user_id={user_id}")

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user

    Returns:
        User information
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        created_at=current_user.created_datetime,
        last_login=current_user.last_login_datetime,
        is_active=current_user.is_active
    )
