"""
Unit tests for audit logging module.

Tests audit event logging, retrieval, filtering, and statistics.
"""

import pytest
import sqlite3
import tempfile
import os
import json
from datetime import datetime, timezone, timedelta

from scrapetui.core.audit import (
    AuditLogger,
    AuditEventType,
    AuditEvent,
    log_audit_event,
    get_audit_logger
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    # Create users table for foreign key
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL
        )
    """)
    conn.execute("INSERT INTO users (id, username) VALUES (1, 'testuser')")
    conn.execute("INSERT INTO users (id, username) VALUES (2, 'admin')")
    conn.commit()
    conn.close()

    yield path

    os.unlink(path)


class TestAuditLogger:
    """Test AuditLogger class."""

    def test_initialization(self, temp_db):
        """Test audit logger initialization."""
        logger = AuditLogger(temp_db)
        assert logger.db_path == temp_db

        # Verify table was created
        conn = sqlite3.connect(temp_db)
        tables = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='audit_log'
        """).fetchone()
        conn.close()

        assert tables is not None

    def test_log_event(self, temp_db):
        """Test logging an audit event."""
        logger = AuditLogger(temp_db)

        event_id = logger.log(
            AuditEventType.LOGIN_SUCCESS,
            user_id=1,
            username='testuser',
            ip_address='127.0.0.1',
            event_data={'browser': 'Firefox'}
        )

        assert event_id is not None
        assert event_id > 0

        # Verify event was stored
        conn = sqlite3.connect(temp_db)
        event = conn.execute("""
            SELECT * FROM audit_log WHERE id = ?
        """, (event_id,)).fetchone()
        conn.close()

        assert event is not None

    def test_log_event_without_user(self, temp_db):
        """Test logging event without user ID."""
        logger = AuditLogger(temp_db)

        event_id = logger.log(
            AuditEventType.LOGIN_FAILURE,
            username='unknown',
            ip_address='192.168.1.1'
        )

        assert event_id > 0

    def test_get_events(self, temp_db):
        """Test retrieving audit events."""
        logger = AuditLogger(temp_db)

        # Log some events
        logger.log(AuditEventType.LOGIN_SUCCESS, user_id=1, username='testuser')
        logger.log(AuditEventType.LOGIN_FAILURE, user_id=1, username='testuser')
        logger.log(AuditEventType.LOGOUT, user_id=1, username='testuser')

        events = logger.get_events(limit=10)
        assert len(events) == 3

    def test_filter_by_user(self, temp_db):
        """Test filtering events by user ID."""
        logger = AuditLogger(temp_db)

        logger.log(AuditEventType.LOGIN_SUCCESS, user_id=1, username='testuser')
        logger.log(AuditEventType.LOGIN_SUCCESS, user_id=2, username='admin')
        logger.log(AuditEventType.LOGOUT, user_id=1, username='testuser')

        events = logger.get_events(user_id=1)
        assert len(events) == 2
        assert all(e['user_id'] == 1 for e in events)

    def test_filter_by_event_type(self, temp_db):
        """Test filtering events by type."""
        logger = AuditLogger(temp_db)

        logger.log(AuditEventType.LOGIN_SUCCESS, user_id=1)
        logger.log(AuditEventType.LOGIN_FAILURE, user_id=1)
        logger.log(AuditEventType.LOGIN_SUCCESS, user_id=2)

        events = logger.get_events(event_type=AuditEventType.LOGIN_SUCCESS)
        assert len(events) == 2
        assert all(e['event_type'] == 'login_success' for e in events)

    def test_filter_by_date_range(self, temp_db):
        """Test filtering events by date range."""
        logger = AuditLogger(temp_db)

        # Log event with specific timestamp
        now = datetime.now(timezone.utc)
        past = (now - timedelta(days=2)).isoformat()
        future = (now + timedelta(days=2)).isoformat()

        logger.log(AuditEventType.LOGIN_SUCCESS, user_id=1)

        # Get events since yesterday
        since = (now - timedelta(days=1)).isoformat()
        events = logger.get_events(since=since)
        assert len(events) == 1

        # Get events until tomorrow
        events = logger.get_events(until=future)
        assert len(events) >= 1

    def test_pagination(self, temp_db):
        """Test event pagination."""
        logger = AuditLogger(temp_db)

        # Log 10 events
        for i in range(10):
            logger.log(AuditEventType.LOGIN_SUCCESS, user_id=1)

        # Get first 5
        events_page1 = logger.get_events(limit=5, offset=0)
        assert len(events_page1) == 5

        # Get next 5
        events_page2 = logger.get_events(limit=5, offset=5)
        assert len(events_page2) == 5

        # Verify different events
        ids_page1 = {e['id'] for e in events_page1}
        ids_page2 = {e['id'] for e in events_page2}
        assert len(ids_page1 & ids_page2) == 0  # No overlap

    def test_event_data_json(self, temp_db):
        """Test JSON event data storage and retrieval."""
        logger = AuditLogger(temp_db)

        event_data = {
            'reason': 'invalid_password',
            'attempts': 3,
            'locked': False
        }

        event_id = logger.log(
            AuditEventType.LOGIN_FAILURE,
            user_id=1,
            event_data=event_data
        )

        events = logger.get_events(limit=1)
        assert len(events) == 1
        assert events[0]['event_data'] == event_data

    def test_get_user_activity(self, temp_db):
        """Test getting user activity."""
        logger = AuditLogger(temp_db)

        # Log events for user 1
        logger.log(AuditEventType.LOGIN_SUCCESS, user_id=1)
        logger.log(AuditEventType.ARTICLE_CREATED, user_id=1)
        logger.log(AuditEventType.LOGOUT, user_id=1)

        # Log event for user 2
        logger.log(AuditEventType.LOGIN_SUCCESS, user_id=2)

        activity = logger.get_user_activity(user_id=1)
        assert len(activity) == 3
        assert all(e['user_id'] == 1 for e in activity)

    def test_get_failed_logins(self, temp_db):
        """Test getting failed login attempts."""
        logger = AuditLogger(temp_db)

        logger.log(
            AuditEventType.LOGIN_FAILURE,
            username='testuser',
            ip_address='127.0.0.1'
        )
        logger.log(
            AuditEventType.LOGIN_FAILURE,
            username='admin',
            ip_address='192.168.1.1'
        )

        failed = logger.get_failed_logins()
        assert len(failed) == 2

        # Filter by username
        failed_user = logger.get_failed_logins(username='testuser')
        assert len(failed_user) == 1
        assert failed_user[0]['username'] == 'testuser'

    def test_cleanup_old_logs(self, temp_db):
        """Test cleaning up old audit logs."""
        logger = AuditLogger(temp_db)

        # Log event
        logger.log(AuditEventType.LOGIN_SUCCESS, user_id=1)

        # Manually set old timestamp
        old_time = (
            datetime.now(timezone.utc) - timedelta(days=100)
        ).isoformat()

        conn = sqlite3.connect(temp_db)
        conn.execute("""
            UPDATE audit_log SET created_at = ?
        """, (old_time,))
        conn.commit()
        conn.close()

        # Cleanup logs older than 90 days
        deleted = logger.cleanup_old_logs(retention_days=90)
        assert deleted == 1

    def test_get_statistics(self, temp_db):
        """Test getting audit log statistics."""
        logger = AuditLogger(temp_db)

        # Log various events
        logger.log(AuditEventType.LOGIN_SUCCESS, user_id=1, username='testuser')
        logger.log(AuditEventType.LOGIN_SUCCESS, user_id=1, username='testuser')
        logger.log(AuditEventType.LOGIN_FAILURE, user_id=2, username='admin')
        logger.log(AuditEventType.LOGOUT, user_id=1, username='testuser')

        stats = logger.get_statistics()

        assert stats['total_events'] == 4
        assert len(stats['events_by_type']) > 0
        assert len(stats['events_by_user']) > 0
        assert stats['last_24h'] == 4  # All recent

    def test_event_ordering(self, temp_db):
        """Test events are returned in descending order."""
        logger = AuditLogger(temp_db)

        # Log events with slight delay
        event1_id = logger.log(AuditEventType.LOGIN_SUCCESS, user_id=1)
        event2_id = logger.log(AuditEventType.LOGOUT, user_id=1)

        events = logger.get_events(limit=2)

        # Most recent first
        assert events[0]['id'] == event2_id
        assert events[1]['id'] == event1_id


class TestAuditEventType:
    """Test AuditEventType enum."""

    def test_event_types_exist(self):
        """Test all expected event types exist."""
        expected_types = [
            'LOGIN_SUCCESS', 'LOGIN_FAILURE', 'LOGOUT',
            'PASSWORD_CHANGED', 'ACCOUNT_LOCKED', 'ACCOUNT_CREATED'
        ]

        for event_type in expected_types:
            assert hasattr(AuditEventType, event_type)

    def test_event_type_values(self):
        """Test event type values are strings."""
        assert AuditEventType.LOGIN_SUCCESS.value == 'login_success'
        assert AuditEventType.LOGIN_FAILURE.value == 'login_failure'
        assert AuditEventType.ACCOUNT_LOCKED.value == 'account_locked'


class TestAuditEvent:
    """Test AuditEvent dataclass."""

    def test_event_creation(self):
        """Test creating audit event."""
        event = AuditEvent(
            event_type='test_event',
            user_id=1,
            username='testuser'
        )

        assert event.event_type == 'test_event'
        assert event.user_id == 1
        assert event.username == 'testuser'
        assert event.created_at is not None

    def test_event_with_data(self):
        """Test event with additional data."""
        event_data = {'key': 'value', 'count': 42}
        event = AuditEvent(
            event_type='test_event',
            event_data=event_data
        )

        assert event.event_data == event_data


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_log_audit_event(self, temp_db):
        """Test log_audit_event convenience function."""
        # Note: This uses the global instance, so we need to be careful
        # In real tests, might want to mock or use dependency injection

        # For now, just test the function exists and has correct signature
        from scrapetui.core.audit import log_audit_event
        assert callable(log_audit_event)

    def test_get_audit_logger(self, temp_db):
        """Test get_audit_logger singleton."""
        logger1 = get_audit_logger(temp_db)
        logger2 = get_audit_logger(temp_db)

        # Should return same instance (singleton)
        assert logger1 is logger2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
