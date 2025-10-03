"""Role-Based Access Control (RBAC) system."""

from typing import Optional

from .database import get_db_connection
from ..utils.logging import get_logger
from ..utils.errors import PermissionError as PermissionDeniedError
from ..constants import Role

logger = get_logger(__name__)


def get_user_role(user_id: int) -> Role:
    """
    Get user's role.

    Args:
        user_id: User ID

    Returns:
        User's role enum value
    """
    with get_db_connection() as conn:
        result = conn.execute(
            "SELECT role FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        if not result:
            return Role.GUEST

        role_str = result[0].upper()
        return Role[role_str] if role_str in Role.__members__ else Role.GUEST


def check_permission(user_id: int, required_role: Role) -> bool:
    """
    Check if user has required role (hierarchical).

    Args:
        user_id: User ID to check
        required_role: Minimum required role

    Returns:
        True if user has sufficient permissions
    """
    user_role = get_user_role(user_id)
    return user_role.value >= required_role.value


def is_admin(user_id: int) -> bool:
    """
    Quick check if user is admin.

    Args:
        user_id: User ID

    Returns:
        True if user has admin role
    """
    return check_permission(user_id, Role.ADMIN)


def is_user_or_higher(user_id: int) -> bool:
    """
    Check if user has USER role or higher.

    Args:
        user_id: User ID

    Returns:
        True if user has USER or ADMIN role
    """
    return check_permission(user_id, Role.USER)


def can_edit(user_id: int, owner_user_id: int) -> bool:
    """
    Check if user can edit resource (admin or owner).

    Args:
        user_id: User ID attempting to edit
        owner_user_id: User ID of resource owner

    Returns:
        True if user can edit
    """
    return is_admin(user_id) or user_id == owner_user_id


def can_delete(user_id: int, owner_user_id: int) -> bool:
    """
    Check if user can delete resource (admin or owner).

    Args:
        user_id: User ID attempting to delete
        owner_user_id: User ID of resource owner

    Returns:
        True if user can delete
    """
    return is_admin(user_id) or user_id == owner_user_id


def can_view_user_data(viewer_id: int, target_user_id: int) -> bool:
    """
    Check if user can view another user's data.

    Args:
        viewer_id: User ID attempting to view
        target_user_id: User ID of data owner

    Returns:
        True if user can view data
    """
    # Admin can view all data
    if is_admin(viewer_id):
        return True

    # Users can view their own data
    if viewer_id == target_user_id:
        return True

    # Check if data is shared (future feature)
    # For now, only owner and admin can view
    return False


def require_role(user_id: int, required_role: Role) -> None:
    """
    Raise exception if user doesn't have required role.

    Args:
        user_id: User ID to check
        required_role: Minimum required role

    Raises:
        PermissionDeniedError: If user lacks required role
    """
    if not check_permission(user_id, required_role):
        user_role = get_user_role(user_id)
        logger.warning(
            f"Permission denied for user_id={user_id} "
            f"(role={user_role.name}, required={required_role.name})"
        )
        raise PermissionDeniedError(
            f"Insufficient permissions. Required role: {required_role.name}"
        )


def require_ownership(user_id: int, owner_user_id: int) -> None:
    """
    Raise exception if user is not admin or owner.

    Args:
        user_id: User ID attempting action
        owner_user_id: User ID of resource owner

    Raises:
        PermissionDeniedError: If user is not admin or owner
    """
    if not can_edit(user_id, owner_user_id):
        logger.warning(
            f"Ownership check failed for user_id={user_id} "
            f"(owner={owner_user_id})"
        )
        raise PermissionDeniedError(
            "You can only modify your own resources or be an administrator"
        )
