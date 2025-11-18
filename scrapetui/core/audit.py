"""
Audit Logging System

Provides comprehensive audit logging for security and administrative events.
Logs user actions, authentication events, and system changes.

Part of v2.2.0 Security Enhancements.
"""

import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum


class AuditEventType(Enum):
    """Audit event types."""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    SESSION_EXPIRED = "session_expired"

    # Password events
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    FORCE_PASSWORD_CHANGE = "force_password_change"

    # Account events
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    ACCOUNT_CREATED = "account_created"
    ACCOUNT_UPDATED = "account_updated"
    ACCOUNT_DELETED = "account_deleted"
    ACCOUNT_ACTIVATED = "account_activated"
    ACCOUNT_DEACTIVATED = "account_deactivated"

    # Data events
    ARTICLE_CREATED = "article_created"
    ARTICLE_DELETED = "article_deleted"
    SCRAPER_CREATED = "scraper_created"
    SCRAPER_DELETED = "scraper_deleted"

    # Administrative events
    USER_ROLE_CHANGED = "user_role_changed"
    QUOTA_CHANGED = "quota_changed"
    QUOTA_EXCEEDED = "quota_exceeded"
    SYSTEM_SETTING_CHANGED = "system_setting_changed"

    # Security events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PERMISSION_DENIED = "permission_denied"


@dataclass
class AuditEvent:
    """Audit event data structure."""
    event_type: str
    user_id: Optional[int] = None
    username: Optional[str] = None
    event_data: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        """Set created_at if not provided."""
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class AuditLogger:
    """Audit logging manager."""

    def __init__(self, db_path: str = "scraped_data_tui_v1.0.db"):
        """
        Initialize audit logger.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._ensure_audit_table()

    def _ensure_audit_table(self):
        """Ensure audit_log table exists."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    event_type TEXT NOT NULL,
                    event_data TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            """)
            # Create indexes for better query performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_user_created
                ON audit_log(user_id, created_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_event_created
                ON audit_log(event_type, created_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_created
                ON audit_log(created_at)
            """)
            conn.commit()

    def log(
        self,
        event_type: AuditEventType,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> int:
        """
        Log an audit event.

        Args:
            event_type: Type of event
            user_id: User ID who performed the action
            username: Username (if user_id not available)
            event_data: Additional event data
            ip_address: IP address of the request
            user_agent: User agent string

        Returns:
            ID of created audit log entry

        Example:
            >>> logger = AuditLogger()
            >>> logger.log(
            ...     AuditEventType.LOGIN_SUCCESS,
            ...     user_id=1,
            ...     username="admin",
            ...     ip_address="127.0.0.1"
            ... )
        """
        event = AuditEvent(
            event_type=event_type.value,
            user_id=user_id,
            username=username,
            event_data=event_data,
            ip_address=ip_address,
            user_agent=user_agent
        )

        event_data_json = json.dumps(event_data) if event_data else None

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO audit_log
                (user_id, username, event_type, event_data, ip_address,
                 user_agent, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                event.user_id,
                event.username,
                event.event_type,
                event_data_json,
                event.ip_address,
                event.user_agent,
                event.created_at
            ))
            conn.commit()
            return cursor.lastrowid

    def get_events(
        self,
        user_id: Optional[int] = None,
        event_type: Optional[AuditEventType] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve audit events with filtering.

        Args:
            user_id: Filter by user ID
            event_type: Filter by event type
            since: Filter events after this timestamp (ISO format)
            until: Filter events before this timestamp (ISO format)
            limit: Maximum number of events to return
            offset: Offset for pagination

        Returns:
            List of audit event dictionaries

        Example:
            >>> logger = AuditLogger()
            >>> events = logger.get_events(
            ...     event_type=AuditEventType.LOGIN_FAILURE,
            ...     limit=10
            ... )
        """
        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []

        if user_id is not None:
            query += " AND user_id = ?"
            params.append(user_id)

        if event_type is not None:
            query += " AND event_type = ?"
            params.append(event_type.value)

        if since:
            query += " AND created_at >= ?"
            params.append(since)

        if until:
            query += " AND created_at <= ?"
            params.append(until)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            events = []
            for row in cursor.fetchall():
                event = dict(row)
                # Parse JSON event_data
                if event.get('event_data'):
                    try:
                        event['event_data'] = json.loads(event['event_data'])
                    except json.JSONDecodeError:
                        pass
                events.append(event)
            return events

    def get_user_activity(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent activity for a user.

        Args:
            user_id: User ID
            limit: Maximum number of events

        Returns:
            List of recent events for the user
        """
        return self.get_events(user_id=user_id, limit=limit)

    def get_failed_logins(
        self,
        username: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get failed login attempts.

        Args:
            username: Optional username filter
            since: Optional timestamp filter
            limit: Maximum number of events

        Returns:
            List of failed login events
        """
        query = """
            SELECT * FROM audit_log
            WHERE event_type = ?
        """
        params = [AuditEventType.LOGIN_FAILURE.value]

        if username:
            query += " AND username = ?"
            params.append(username)

        if since:
            query += " AND created_at >= ?"
            params.append(since)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            events = []
            for row in cursor.fetchall():
                event = dict(row)
                if event.get('event_data'):
                    try:
                        event['event_data'] = json.loads(event['event_data'])
                    except json.JSONDecodeError:
                        pass
                events.append(event)
            return events

    def cleanup_old_logs(self, retention_days: int = 90) -> int:
        """
        Remove audit logs older than retention period.

        Args:
            retention_days: Number of days to retain logs

        Returns:
            Number of logs deleted
        """
        cutoff = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        cutoff = cutoff.replace(day=cutoff.day - retention_days)
        cutoff_iso = cutoff.isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM audit_log
                WHERE created_at < ?
            """, (cutoff_iso,))
            conn.commit()
            return cursor.rowcount

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get audit log statistics.

        Returns:
            Dictionary with statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Total events
            total = conn.execute(
                "SELECT COUNT(*) as count FROM audit_log"
            ).fetchone()['count']

            # Events by type (top 10)
            by_type = conn.execute("""
                SELECT event_type, COUNT(*) as count
                FROM audit_log
                GROUP BY event_type
                ORDER BY count DESC
                LIMIT 10
            """).fetchall()

            # Events by user (top 10)
            by_user = conn.execute("""
                SELECT user_id, username, COUNT(*) as count
                FROM audit_log
                WHERE user_id IS NOT NULL
                GROUP BY user_id
                ORDER BY count DESC
                LIMIT 10
            """).fetchall()

            # Recent events (last 24 hours)
            since_24h = datetime.now(timezone.utc).replace(
                hour=datetime.now(timezone.utc).hour - 24
            ).isoformat()
            recent = conn.execute("""
                SELECT COUNT(*) as count
                FROM audit_log
                WHERE created_at >= ?
            """, (since_24h,)).fetchone()['count']

            return {
                'total_events': total,
                'events_by_type': [dict(row) for row in by_type],
                'events_by_user': [dict(row) for row in by_user],
                'last_24h': recent
            }


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger(db_path: str = "scraped_data_tui_v1.0.db") -> AuditLogger:
    """
    Get or create global audit logger instance.

    Args:
        db_path: Path to database

    Returns:
        AuditLogger instance
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(db_path)
    return _audit_logger


def log_audit_event(
    event_type: AuditEventType,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    event_data: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> int:
    """
    Convenience function to log an audit event.

    Args:
        event_type: Type of event
        user_id: User ID
        username: Username
        event_data: Additional data
        ip_address: IP address
        user_agent: User agent

    Returns:
        ID of created log entry
    """
    logger = get_audit_logger()
    return logger.log(
        event_type,
        user_id=user_id,
        username=username,
        event_data=event_data,
        ip_address=ip_address,
        user_agent=user_agent
    )
