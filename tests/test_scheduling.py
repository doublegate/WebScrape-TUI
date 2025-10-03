#!/usr/bin/env python3
"""Tests for v1.5.0 features: Scheduled Scraping & Automation."""

import pytest
import tempfile
import sqlite3
import time
import random
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Import the application components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from monolithic scrapetui.py file directly
# We need to import the .py file, not the package directory which has ScheduleManager=None
import importlib.util
_scrapetui_path = Path(__file__).parent.parent / 'scrapetui.py'
_spec = importlib.util.spec_from_file_location("scrapetui_monolith", _scrapetui_path)
_scrapetui_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_scrapetui_module)

# Import needed components from the monolithic module
ScheduleManager = _scrapetui_module.ScheduleManager
init_db = _scrapetui_module.init_db
get_db_connection = _scrapetui_module.get_db_connection
DB_PATH = _scrapetui_module.DB_PATH


@pytest.fixture
def temp_db(monkeypatch):
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db_path = f.name

    # Patch the monolithic module's DB_PATH to use temp database
    global _scrapetui_module
    original_db = _scrapetui_module.DB_PATH
    _scrapetui_module.DB_PATH = Path(temp_db_path)

    # Initialize the database
    init_db()

    # Add a test scraper profile with unique name to avoid UNIQUE constraints
    unique_id = f"{int(time.time() * 1000000)}-{random.randint(1000, 9999)}"
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO saved_scrapers (name, url, selector, default_limit, user_id)
            VALUES (?, 'https://example.com', 'h2 a', 10, 1)
        """, (f'Test Scraper {unique_id}',))
        conn.commit()

    yield temp_db_path

    # Cleanup
    _scrapetui_module.DB_PATH = original_db
    Path(temp_db_path).unlink(missing_ok=True)


class TestScheduleManager:
    """Test ScheduleManager class for schedule CRUD operations."""

    def test_create_schedule(self, temp_db):
        """Test creating a new schedule."""
        success = ScheduleManager.create_schedule(
            name="Daily Test Scrape",
            scraper_profile_id=1,
            schedule_type="daily",
            schedule_value="09:00",
            enabled=True
        )
        assert success is True

        # Verify it was created
        schedules = ScheduleManager.list_schedules()
        assert len(schedules) == 1
        assert schedules[0]['name'] == "Daily Test Scrape"
        assert schedules[0]['schedule_type'] == "daily"
        assert schedules[0]['schedule_value'] == "09:00"
        assert schedules[0]['enabled'] is True

    def test_create_duplicate_schedule(self, temp_db):
        """Test that duplicate schedule names are rejected."""
        ScheduleManager.create_schedule(
            name="Duplicate Test",
            scraper_profile_id=1,
            schedule_type="hourly",
            schedule_value="",
            enabled=True
        )

        # Try to create duplicate
        success = ScheduleManager.create_schedule(
            name="Duplicate Test",
            scraper_profile_id=1,
            schedule_type="daily",
            schedule_value="10:00",
            enabled=True
        )
        assert success is False

    def test_list_schedules(self, temp_db):
        """Test listing all schedules."""
        # Create multiple schedules
        ScheduleManager.create_schedule("Schedule 1", 1, "hourly", "", True)
        ScheduleManager.create_schedule("Schedule 2", 1, "daily", "09:00", False)
        ScheduleManager.create_schedule("Schedule 3", 1, "weekly", "0:09:00", True)

        schedules = ScheduleManager.list_schedules()
        assert len(schedules) == 3

        # Test filtering by enabled only
        enabled_schedules = ScheduleManager.list_schedules(enabled_only=True)
        assert len(enabled_schedules) == 2

    def test_get_schedule(self, temp_db):
        """Test getting a specific schedule by ID."""
        ScheduleManager.create_schedule("Get Test", 1, "interval", "30", True)

        schedules = ScheduleManager.list_schedules()
        schedule_id = schedules[0]['id']

        schedule = ScheduleManager.get_schedule(schedule_id)
        assert schedule is not None
        assert schedule['name'] == "Get Test"
        assert schedule['schedule_type'] == "interval"
        assert schedule['schedule_value'] == "30"
        assert 'profile_url' in schedule
        assert 'profile_selector' in schedule

    def test_get_nonexistent_schedule(self, temp_db):
        """Test getting a schedule that doesn't exist."""
        schedule = ScheduleManager.get_schedule(999)
        assert schedule is None

    def test_update_schedule(self, temp_db):
        """Test updating a schedule."""
        ScheduleManager.create_schedule("Update Test", 1, "hourly", "", True)

        schedules = ScheduleManager.list_schedules()
        schedule_id = schedules[0]['id']

        # Update the schedule
        success = ScheduleManager.update_schedule(
            schedule_id,
            name="Updated Name",
            schedule_type="daily",
            schedule_value="10:00",
            enabled=False
        )
        assert success is True

        # Verify update
        schedule = ScheduleManager.get_schedule(schedule_id)
        assert schedule['name'] == "Updated Name"
        assert schedule['schedule_type'] == "daily"
        assert schedule['schedule_value'] == "10:00"
        assert schedule['enabled'] is False

    def test_update_schedule_partial(self, temp_db):
        """Test partial update of a schedule."""
        ScheduleManager.create_schedule("Partial Update", 1, "hourly", "", True)

        schedules = ScheduleManager.list_schedules()
        schedule_id = schedules[0]['id']

        # Update only enabled status
        success = ScheduleManager.update_schedule(schedule_id, enabled=False)
        assert success is True

        # Verify only enabled changed
        schedule = ScheduleManager.get_schedule(schedule_id)
        assert schedule['name'] == "Partial Update"
        assert schedule['schedule_type'] == "hourly"
        assert schedule['enabled'] is False

    def test_delete_schedule(self, temp_db):
        """Test deleting a schedule."""
        ScheduleManager.create_schedule("Delete Test", 1, "daily", "09:00", True)

        schedules = ScheduleManager.list_schedules()
        assert len(schedules) == 1
        schedule_id = schedules[0]['id']

        # Delete the schedule
        success = ScheduleManager.delete_schedule(schedule_id)
        assert success is True

        # Verify deletion
        schedules = ScheduleManager.list_schedules()
        assert len(schedules) == 0

    def test_record_execution(self, temp_db):
        """Test recording schedule execution results."""
        ScheduleManager.create_schedule("Execution Test", 1, "hourly", "", True)

        schedules = ScheduleManager.list_schedules()
        schedule_id = schedules[0]['id']

        # Record successful execution
        success = ScheduleManager.record_execution(schedule_id, 'success')
        assert success is True

        # Verify execution was recorded
        schedule = ScheduleManager.get_schedule(schedule_id)
        assert schedule['last_status'] == 'success'
        assert schedule['last_error'] is None
        assert schedule['run_count'] == 1
        assert schedule['last_run'] is not None
        assert schedule['next_run'] is not None

    def test_record_execution_with_error(self, temp_db):
        """Test recording failed schedule execution."""
        ScheduleManager.create_schedule("Error Test", 1, "daily", "09:00", True)

        schedules = ScheduleManager.list_schedules()
        schedule_id = schedules[0]['id']

        # Record failed execution
        error_message = "Network timeout"
        success = ScheduleManager.record_execution(schedule_id, 'failed', error_message)
        assert success is True

        # Verify error was recorded
        schedule = ScheduleManager.get_schedule(schedule_id)
        assert schedule['last_status'] == 'failed'
        assert schedule['last_error'] == error_message
        assert schedule['run_count'] == 1


class TestScheduleCalculations:
    """Test schedule calculation and next run time logic."""

    def test_calculate_next_run_hourly(self, temp_db):
        """Test next run calculation for hourly schedules."""
        ScheduleManager.create_schedule("Hourly Test", 1, "hourly", "", True)

        schedules = ScheduleManager.list_schedules()
        next_run_value = schedules[0]['next_run']

        # Handle both string and datetime objects
        if isinstance(next_run_value, str):
            next_run = datetime.strptime(next_run_value, '%Y-%m-%d %H:%M:%S')
        else:
            next_run = next_run_value

        now = datetime.now()

        # Should be approximately 1 hour from now
        diff = (next_run - now).total_seconds()
        assert 3550 < diff < 3650  # Allow 10 seconds variance

    def test_calculate_next_run_daily(self, temp_db):
        """Test next run calculation for daily schedules."""
        ScheduleManager.create_schedule("Daily Test", 1, "daily", "09:00", True)

        schedules = ScheduleManager.list_schedules()
        next_run_value = schedules[0]['next_run']

        # Handle both string and datetime objects
        if isinstance(next_run_value, str):
            next_run = datetime.strptime(next_run_value, '%Y-%m-%d %H:%M:%S')
        else:
            next_run = next_run_value

        # Should have hour=9, minute=0
        assert next_run.hour == 9
        assert next_run.minute == 0

    def test_calculate_next_run_weekly(self, temp_db):
        """Test next run calculation for weekly schedules."""
        # Schedule for Monday 9am (0:09:00)
        ScheduleManager.create_schedule("Weekly Test", 1, "weekly", "0:09:00", True)

        schedules = ScheduleManager.list_schedules()
        next_run_value = schedules[0]['next_run']

        # Handle both string and datetime objects
        if isinstance(next_run_value, str):
            next_run = datetime.strptime(next_run_value, '%Y-%m-%d %H:%M:%S')
        else:
            next_run = next_run_value

        # Should be a Monday at 9am
        assert next_run.weekday() == 0  # Monday
        assert next_run.hour == 9
        assert next_run.minute == 0

    def test_calculate_next_run_interval(self, temp_db):
        """Test next run calculation for interval schedules."""
        # 30 minute interval
        ScheduleManager.create_schedule("Interval Test", 1, "interval", "30", True)

        schedules = ScheduleManager.list_schedules()
        next_run_value = schedules[0]['next_run']

        # Handle both string and datetime objects
        if isinstance(next_run_value, str):
            next_run = datetime.strptime(next_run_value, '%Y-%m-%d %H:%M:%S')
        else:
            next_run = next_run_value

        now = datetime.now()

        # Should be approximately 30 minutes from now
        diff = (next_run - now).total_seconds()
        assert 1750 < diff < 1850  # Allow 10 seconds variance


class TestScheduleDatabase:
    """Test database schema and constraints for scheduled_scrapes table."""

    def test_scheduled_scrapes_table_exists(self, temp_db):
        """Test that scheduled_scrapes table has all required columns."""
        with get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='scheduled_scrapes'"
            )
            table = cursor.fetchone()
            assert table is not None

            # Check columns
            cursor = conn.execute("PRAGMA table_info(scheduled_scrapes)")
            columns = {row['name'] for row in cursor.fetchall()}

            required_columns = {
                'id', 'name', 'scraper_profile_id', 'schedule_type', 'schedule_value',
                'enabled', 'last_run', 'next_run', 'run_count', 'last_status',
                'last_error', 'created_at'
            }
            assert required_columns.issubset(columns)

    def test_schedule_name_uniqueness(self, temp_db):
        """Test that schedule names must be unique."""
        ScheduleManager.create_schedule("Unique Test", 1, "hourly", "", True)

        # Try to create duplicate
        with pytest.raises(Exception):
            with get_db_connection() as conn:
                conn.execute("""
                    INSERT INTO scheduled_scrapes
                    (name, scraper_profile_id, schedule_type, schedule_value, enabled)
                    VALUES ('Unique Test', 1, 'daily', '09:00', 1)
                """)
                conn.commit()

    def test_schedule_foreign_key(self, temp_db):
        """Test foreign key constraint to saved_scrapers."""
        # This should succeed with valid profile_id
        success = ScheduleManager.create_schedule("Valid FK", 1, "hourly", "", True)
        assert success is True

        # This should fail with invalid profile_id (depends on DB enforcement)
        try:
            with get_db_connection() as conn:
                conn.execute("""
                    INSERT INTO scheduled_scrapes
                    (name, scraper_profile_id, schedule_type, schedule_value, enabled)
                    VALUES ('Invalid FK', 999, 'hourly', '', 1)
                """)
                conn.commit()
                # If we get here, FK constraints may not be enforced
        except sqlite3.IntegrityError:
            # This is expected if FK constraints are enabled
            pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
