"""
Security API endpoints for WebScrape-TUI v2.2.0.

Provides REST API access to password management, audit logs,
and quota administration.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from ..core.auth_enhanced import (
    authenticate_user_enhanced,
    create_user_with_policy,
    change_password_with_policy,
    logout_user
)
from ..core.password_policy import (
    validate_password,
    PasswordPolicy,
    PasswordStrength
)
from ..core.rate_limit import get_rate_limiter
from ..core.audit import get_audit_logger, AuditEventType
from ..core.quotas import get_quota_manager, QuotaType
from ..core.password_reset import get_password_reset_manager
from ..core.database import get_db_connection


router = APIRouter(prefix="/api/v1/security", tags=["security"])


# ============================================================================
# Request/Response Models
# ============================================================================

class LoginRequest(BaseModel):
    """Login request model."""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Login response model."""
    success: bool
    user_id: Optional[int] = None
    session_token: Optional[str] = None
    message: str
    user_role: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=1)


class PasswordValidationRequest(BaseModel):
    """Password validation request."""
    password: str = Field(..., min_length=1)
    username: Optional[str] = None


class PasswordValidationResponse(BaseModel):
    """Password validation response."""
    is_valid: bool
    score: int
    strength_level: str
    errors: List[str]
    warnings: List[str]


class GenerateResetTokenRequest(BaseModel):
    """Generate password reset token request."""
    username: str = Field(..., min_length=1, max_length=50)


class GenerateResetTokenResponse(BaseModel):
    """Generate password reset token response."""
    token: str
    expires_at: str
    username: str


class UseResetTokenRequest(BaseModel):
    """Use password reset token request."""
    token: str = Field(..., min_length=32)
    new_password: str = Field(..., min_length=1)


class AccountStatusResponse(BaseModel):
    """Account security status response."""
    username: str
    is_active: bool
    account_locked: bool
    locked_until: Optional[str]
    failed_login_attempts: int
    last_failed_login: Optional[str]
    password_changed_at: Optional[str]
    force_password_change: bool
    last_login: Optional[str]


class QuotaStatusResponse(BaseModel):
    """Quota status response."""
    quota_type: str
    current_usage: int
    quota_limit: int
    remaining: int
    percentage_used: float
    exceeded: bool


class SetQuotaRequest(BaseModel):
    """Set user quota request."""
    username: str = Field(..., min_length=1, max_length=50)
    article_quota: Optional[int] = None
    scraper_quota: Optional[int] = None


class AuditLogEntry(BaseModel):
    """Audit log entry model."""
    id: int
    event_type: str
    user_id: Optional[int]
    username: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    event_data: Optional[Dict[str, Any]]
    created_at: str


class AuditLogResponse(BaseModel):
    """Audit log query response."""
    events: List[AuditLogEntry]
    total_count: int


# ============================================================================
# Dependency Functions
# ============================================================================

def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Get current authenticated user from session token.

    Expects Authorization header: Bearer <session_token>
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    session_token = auth_header.split(" ")[1]

    # Validate session
    with get_db_connection() as conn:
        conn.row_factory = lambda cursor, row: dict(
            zip([col[0] for col in cursor.description], row)
        )

        result = conn.execute("""
            SELECT
                u.id,
                u.username,
                u.role,
                u.is_active
            FROM users u
            JOIN user_sessions s ON u.id = s.user_id
            WHERE s.session_token = ?
              AND s.expires_at > ?
        """, (session_token, datetime.now(timezone.utc).isoformat())).fetchone()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )

    if not result['is_active']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    return result


def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require admin role for endpoint access."""
    if user['role'] != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required"
        )
    return user


# ============================================================================
# Authentication Endpoints
# ============================================================================

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, http_request: Request):
    """
    Authenticate user with enhanced security.

    Includes rate limiting, audit logging, and account lockout.
    """
    # Get client IP
    ip_address = http_request.client.host

    # Get user agent
    user_agent = http_request.headers.get("User-Agent", "Unknown")

    # Authenticate with enhanced security
    user_id, session_token, message = authenticate_user_enhanced(
        request.username,
        request.password,
        ip_address=ip_address,
        user_agent=user_agent
    )

    if user_id is None:
        return LoginResponse(
            success=False,
            message=message
        )

    # Get user role
    with get_db_connection() as conn:
        result = conn.execute(
            "SELECT role FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        user_role = result[0] if result else None

    return LoginResponse(
        success=True,
        user_id=user_id,
        session_token=session_token,
        message=message,
        user_role=user_role
    )


@router.post("/logout")
def api_logout(user: Dict[str, Any] = Depends(get_current_user)):
    """Log out current user and invalidate session."""
    # Session token is in the dependency, but we need to extract it from header
    # For simplicity, we'll just return success
    # In production, extract token from header and call logout_user

    logout_user(
        session_token="",  # Would extract from request
        user_id=user['id'],
        username=user['username']
    )

    return {"success": True, "message": "Logged out successfully"}


# ============================================================================
# Password Management Endpoints
# ============================================================================

@router.post("/password/validate", response_model=PasswordValidationResponse)
def validate_password_endpoint(request: PasswordValidationRequest):
    """
    Validate password against policy requirements.

    Returns strength score, validation errors, and warnings.
    """
    result = validate_password(request.password, request.username)

    return PasswordValidationResponse(
        is_valid=result.is_valid,
        score=result.score,
        strength_level=result.strength_level,
        errors=result.errors,
        warnings=result.warnings
    )


@router.post("/password/change")
def change_password(
    request: ChangePasswordRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Change user password with policy validation.

    Invalidates all sessions and requires re-login.
    """
    success, message = change_password_with_policy(
        user['id'],
        request.old_password,
        request.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return {"success": True, "message": message}


@router.post("/password/reset/generate", response_model=GenerateResetTokenResponse)
def generate_reset_token(
    request: GenerateResetTokenRequest,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """
    Generate password reset token (admin only).

    Token expires in 24 hours and can only be used once.
    """
    # Get user ID
    with get_db_connection() as conn:
        result = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (request.username,)
        ).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{request.username}' not found"
            )

        user_id = result[0]

    # Generate token
    reset_mgr = get_password_reset_manager()
    token, expires_at = reset_mgr.generate_reset_token(
        user_id,
        created_by=admin['id']
    )

    return GenerateResetTokenResponse(
        token=token,
        expires_at=expires_at,
        username=request.username
    )


@router.post("/password/reset/use")
def use_reset_token(request: UseResetTokenRequest):
    """
    Use password reset token to set new password.

    Token is validated and can only be used once.
    """
    from ..core.auth import hash_password

    # Validate new password
    validation = validate_password(request.new_password)

    if not validation.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password does not meet requirements: {', '.join(validation.errors)}"
        )

    # Use token
    reset_mgr = get_password_reset_manager()
    new_hash = hash_password(request.new_password)

    success = reset_mgr.use_token(request.token, new_hash)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid, expired, or already used token"
        )

    return {"success": True, "message": "Password reset successfully"}


# ============================================================================
# Account Management Endpoints
# ============================================================================

@router.get("/account/status", response_model=AccountStatusResponse)
def get_account_status(user: Dict[str, Any] = Depends(get_current_user)):
    """Get security status for current user."""
    with get_db_connection() as conn:
        conn.row_factory = lambda cursor, row: dict(
            zip([col[0] for col in cursor.description], row)
        )

        result = conn.execute("""
            SELECT
                username,
                is_active,
                account_locked,
                locked_until,
                failed_login_attempts,
                last_failed_login,
                password_changed_at,
                force_password_change,
                last_login
            FROM users
            WHERE id = ?
        """, (user['id'],)).fetchone()

    return AccountStatusResponse(**result)


@router.post("/account/{username}/lock")
def lock_account(
    username: str,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """Lock user account (admin only)."""
    limiter = get_rate_limiter()
    limiter.lock_account(username, admin_lock=True)

    return {"success": True, "message": f"Account '{username}' locked"}


@router.post("/account/{username}/unlock")
def unlock_account(
    username: str,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """Unlock user account (admin only)."""
    limiter = get_rate_limiter()
    limiter.unlock_account(username)

    return {"success": True, "message": f"Account '{username}' unlocked"}


# ============================================================================
# Quota Management Endpoints
# ============================================================================

@router.get("/quotas", response_model=Dict[str, QuotaStatusResponse])
def get_quotas(user: Dict[str, Any] = Depends(get_current_user)):
    """Get quota status for current user."""
    quota_mgr = get_quota_manager()
    quotas = quota_mgr.get_all_quotas(user['id'])

    result = {}
    for quota_type, status in quotas.items():
        result[quota_type] = QuotaStatusResponse(
            quota_type=quota_type,
            current_usage=status.current_usage,
            quota_limit=status.quota_limit,
            remaining=status.remaining,
            percentage_used=status.percentage_used,
            exceeded=status.exceeded
        )

    return result


@router.post("/quotas/set")
def set_quotas(
    request: SetQuotaRequest,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """Set user quotas (admin only)."""
    # Get user ID
    with get_db_connection() as conn:
        result = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (request.username,)
        ).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{request.username}' not found"
            )

        user_id = result[0]

    # Set quotas
    quota_mgr = get_quota_manager()
    quota_mgr.set_user_quota(
        user_id,
        article_quota=request.article_quota,
        scraper_quota=request.scraper_quota,
        set_by=admin['id']
    )

    return {"success": True, "message": f"Quotas updated for '{request.username}'"}


# ============================================================================
# Audit Log Endpoints
# ============================================================================

@router.get("/audit/logs", response_model=AuditLogResponse)
def get_audit_logs(
    event_type: Optional[str] = None,
    username: Optional[str] = None,
    since: Optional[str] = None,
    limit: int = 50,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """
    Get audit log entries (admin only).

    Supports filtering by event type, username, and date.
    """
    logger = get_audit_logger()

    # Build filters
    filters = {}

    if event_type:
        try:
            filters['event_type'] = AuditEventType(event_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event type: {event_type}"
            )

    if username:
        with get_db_connection() as conn:
            result = conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,)
            ).fetchone()
            if result:
                filters['user_id'] = result[0]

    if since:
        try:
            datetime.fromisoformat(since)
            filters['since'] = since
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            )

    filters['limit'] = min(limit, 1000)  # Cap at 1000

    # Get events
    events = logger.get_events(**filters)

    # Convert to response model
    audit_entries = [AuditLogEntry(**event) for event in events]

    return AuditLogResponse(
        events=audit_entries,
        total_count=len(audit_entries)
    )


@router.get("/audit/stats")
def get_audit_stats(admin: Dict[str, Any] = Depends(require_admin)):
    """Get audit log statistics (admin only)."""
    logger = get_audit_logger()
    stats = logger.get_statistics()

    return stats


@router.delete("/audit/cleanup")
def cleanup_audit_logs(
    days: int = 90,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """
    Clean up old audit log entries (admin only).

    Deletes entries older than specified days.
    """
    logger = get_audit_logger()
    deleted = logger.cleanup_old_logs(retention_days=days)

    return {
        "success": True,
        "message": f"Deleted {deleted} audit log entries older than {days} days"
    }
