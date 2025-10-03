"""Session model for WebScrape-TUI."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Session:
    """User session model representing an active session."""

    id: int
    session_token: str
    user_id: int
    created_at: str
    expires_at: str
    ip_address: Optional[str] = None

    @property
    def created_datetime(self) -> datetime:
        """
        Get created_at as datetime object.

        Returns:
            Creation datetime
        """
        return datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))

    @property
    def expires_datetime(self) -> datetime:
        """
        Get expires_at as datetime object.

        Returns:
            Expiration datetime
        """
        return datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))

    @property
    def is_expired(self) -> bool:
        """
        Check if session is expired.

        Returns:
            True if session is expired
        """
        return datetime.now() > self.expires_datetime

    @property
    def time_remaining(self) -> Optional[float]:
        """
        Get remaining time in seconds (None if expired).

        Returns:
            Remaining time in seconds or None
        """
        if self.is_expired:
            return None
        delta = self.expires_datetime - datetime.now()
        return delta.total_seconds()

    def to_dict(self) -> dict:
        """
        Convert to dictionary (without token for security).

        Returns:
            Dictionary representation without session token
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'ip_address': self.ip_address,
            'is_expired': self.is_expired,
            'time_remaining': self.time_remaining
        }

    @classmethod
    def from_db_row(cls, row) -> 'Session':
        """
        Create Session from database row.

        Args:
            row: SQLite row object

        Returns:
            Session instance
        """
        return cls(
            id=row['id'],
            session_token=row['session_token'],
            user_id=row['user_id'],
            created_at=row['created_at'],
            expires_at=row['expires_at'],
            ip_address=row.get('ip_address')
        )

    def __repr__(self) -> str:
        """String representation."""
        status = "expired" if self.is_expired else "active"
        return f"Session(id={self.id}, user_id={self.user_id}, status='{status}')"
