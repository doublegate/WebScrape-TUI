"""User model for WebScrape-TUI."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class Role(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


@dataclass
class User:
    """User model representing a system user."""

    id: int
    username: str
    password_hash: str
    email: Optional[str]
    role: str
    created_at: str
    last_login: Optional[str]
    is_active: bool

    @property
    def role_enum(self) -> Role:
        """
        Get role as enum.

        Returns:
            Role enum value
        """
        return Role(self.role)

    @property
    def created_datetime(self) -> datetime:
        """
        Get created_at as datetime object.

        Returns:
            Creation datetime
        """
        return datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))

    @property
    def last_login_datetime(self) -> Optional[datetime]:
        """
        Get last_login as datetime object.

        Returns:
            Last login datetime or None
        """
        if self.last_login:
            return datetime.fromisoformat(self.last_login.replace('Z', '+00:00'))
        return None

    def to_dict(self) -> dict:
        """
        Convert to dictionary (without password_hash for security).

        Returns:
            Dictionary representation without password
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'is_active': self.is_active
        }

    @classmethod
    def from_db_row(cls, row) -> 'User':
        """
        Create User from database row.

        Args:
            row: SQLite row object

        Returns:
            User instance
        """
        return cls(
            id=row['id'],
            username=row['username'],
            password_hash=row['password_hash'],
            email=row['email'],
            role=row['role'],
            created_at=row['created_at'],
            last_login=row.get('last_login'),
            is_active=bool(row['is_active'])
        )

    def __repr__(self) -> str:
        """String representation."""
        return f"User(id={self.id}, username='{self.username}', role='{self.role}')"
