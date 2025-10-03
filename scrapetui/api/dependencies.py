"""FastAPI dependencies for authentication and authorization."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from ..core.database import get_db_connection
from ..core.permissions import check_permission, is_admin
from ..models.user import User
from ..constants import Role
from ..config import get_config
from ..utils.logging import get_logger
from .exceptions import UnauthorizedException, ForbiddenException

logger = get_logger(__name__)
config = get_config()

# Security scheme
security = HTTPBearer()

# JWT configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.

    Args:
        data: Data to encode in token
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})

    encoded_jwt = jwt.encode(to_encode, config.api_jwt_secret, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create JWT refresh token.

    Args:
        data: Data to encode in token

    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})

    encoded_jwt = jwt.encode(to_encode, config.api_jwt_secret, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decode and verify JWT token.

    Args:
        token: JWT token to decode

    Returns:
        Decoded token payload

    Raises:
        UnauthorizedException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, config.api_jwt_secret, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise UnauthorizedException(detail="Invalid or expired token")


def is_token_blacklisted(token: str) -> bool:
    """
    Check if token is blacklisted.

    Args:
        token: JWT token to check

    Returns:
        True if blacklisted
    """
    try:
        with get_db_connection() as conn:
            result = conn.execute(
                "SELECT COUNT(*) as cnt FROM token_blacklist WHERE token = ?",
                (token,)
            ).fetchone()
            return result['cnt'] > 0
    except Exception as e:
        logger.error(f"Error checking token blacklist: {e}")
        return False


def blacklist_token(token: str) -> None:
    """
    Add token to blacklist.

    Args:
        token: JWT token to blacklist
    """
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO token_blacklist (token, blacklisted_at) VALUES (?, ?)",
                (token, datetime.utcnow().isoformat())
            )
            conn.commit()
            logger.info("Token blacklisted successfully")
    except Exception as e:
        logger.error(f"Error blacklisting token: {e}")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP bearer token credentials

    Returns:
        User object

    Raises:
        UnauthorizedException: If authentication fails
    """
    token = credentials.credentials

    # Check if token is blacklisted
    if is_token_blacklisted(token):
        raise UnauthorizedException(detail="Token has been revoked")

    # Decode token
    payload = decode_token(token)

    # Verify token type
    if payload.get("type") != "access":
        raise UnauthorizedException(detail="Invalid token type")

    # Get user ID
    user_id: int = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException(detail="Invalid token payload")

    # Get user from database
    try:
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ? AND is_active = 1",
                (user_id,)
            ).fetchone()

            if not row:
                raise UnauthorizedException(detail="User not found or inactive")

            return User.from_db_row(row)

    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        raise UnauthorizedException(detail="Authentication failed")


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Require admin role.

    Args:
        current_user: Current authenticated user

    Returns:
        User object

    Raises:
        ForbiddenException: If user is not admin
    """
    if not is_admin(current_user.id):
        raise ForbiddenException(detail="Admin role required")

    return current_user


async def require_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Require user role or higher.

    Args:
        current_user: Current authenticated user

    Returns:
        User object

    Raises:
        ForbiddenException: If user doesn't have USER role
    """
    if not check_permission(current_user.id, Role.USER):
        raise ForbiddenException(detail="User role required")

    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise (for optional auth endpoints).

    Args:
        credentials: Optional HTTP bearer credentials

    Returns:
        User object or None
    """
    if not credentials:
        return None

    try:
        return get_current_user(credentials)
    except:
        return None
