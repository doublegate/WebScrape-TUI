#!/usr/bin/env python3
"""Tests for bulk operations functionality."""

import sqlite3
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_db_with_data():
    """Create a temporary database with test data."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    # Create and populate database
    with sqlite3.connect(db_path) as conn:
        # Create table
        conn.execute("""
            CREATE TABLE scraped_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                title TEXT,
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert test data
        test_articles = [
            (f'https://example.com/{i}', f'Article {i}', f'Content {i}')
            for i in range(1, 11)  # 10 test articles
        ]
        conn.executemany(
            "INSERT INTO scraped_data (url, title, content) VALUES (?, ?, ?)",
            test_articles
        )
        conn.commit()

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


class TestBulkSelection:
    """Test bulk selection functionality."""

    def test_select_multiple_rows(self):
        """Test selecting multiple rows."""
        selected_ids = set()

        # Simulate selecting rows
        selected_ids.add(1)
        selected_ids.add(2)
        selected_ids.add(3)

        assert len(selected_ids) == 3
        assert 1 in selected_ids
        assert 2 in selected_ids
        assert 3 in selected_ids

    def test_toggle_selection(self):
        """Test toggling row selection."""
        selected_ids = set()

        # Add row
        selected_ids.add(1)
        assert 1 in selected_ids

        # Remove row (toggle off)
        selected_ids.discard(1)
        assert 1 not in selected_ids

    def test_select_all(self, temp_db_with_data):
        """Test select all functionality."""
        with sqlite3.connect(temp_db_with_data) as conn:
            cursor = conn.execute("SELECT id FROM scraped_data")
            all_ids = set(row[0] for row in cursor.fetchall())

        assert len(all_ids) == 10
        assert all(i in all_ids for i in range(1, 11))

    def test_deselect_all(self):
        """Test deselect all functionality."""
        selected_ids = {1, 2, 3, 4, 5}

        # Clear all
        selected_ids.clear()

        assert len(selected_ids) == 0


class TestBulkDelete:
    """Test bulk delete operations."""

    def test_bulk_delete_query_syntax(self, temp_db_with_data):
        """Test bulk delete SQL query syntax."""
        selected_ids = [1, 3, 5, 7, 9]

        with sqlite3.connect(temp_db_with_data) as conn:
            # Test the bulk delete query
            placeholders = ','.join('?' * len(selected_ids))
            cursor = conn.execute(
                f"DELETE FROM scraped_data WHERE id IN ({placeholders})",
                selected_ids
            )
            conn.commit()

            assert cursor.rowcount == 5

            # Verify remaining articles
            remaining = conn.execute("SELECT COUNT(*) FROM scraped_data").fetchone()[0]
            assert remaining == 5

    def test_bulk_delete_all(self, temp_db_with_data):
        """Test deleting all articles."""
        with sqlite3.connect(temp_db_with_data) as conn:
            # Get all IDs
            cursor = conn.execute("SELECT id FROM scraped_data")
            all_ids = [row[0] for row in cursor.fetchall()]

            # Delete all
            placeholders = ','.join('?' * len(all_ids))
            cursor = conn.execute(
                f"DELETE FROM scraped_data WHERE id IN ({placeholders})",
                all_ids
            )
            conn.commit()

            # Verify all deleted
            remaining = conn.execute("SELECT COUNT(*) FROM scraped_data").fetchone()[0]
            assert remaining == 0

    def test_bulk_delete_with_empty_selection(self, temp_db_with_data):
        """Test bulk delete with no selection."""
        selected_ids = []

        # Should handle empty list gracefully
        if selected_ids:
            with sqlite3.connect(temp_db_with_data) as conn:
                placeholders = ','.join('?' * len(selected_ids))
                conn.execute(
                    f"DELETE FROM scraped_data WHERE id IN ({placeholders})",
                    selected_ids
                )

        # Verify nothing deleted
        with sqlite3.connect(temp_db_with_data) as conn:
            count = conn.execute("SELECT COUNT(*) FROM scraped_data").fetchone()[0]
            assert count == 10

    def test_bulk_delete_partial_selection(self, temp_db_with_data):
        """Test bulk delete with partial selection."""
        selected_ids = [2, 4, 6]

        with sqlite3.connect(temp_db_with_data) as conn:
            placeholders = ','.join('?' * len(selected_ids))
            cursor = conn.execute(
                f"DELETE FROM scraped_data WHERE id IN ({placeholders})",
                selected_ids
            )
            conn.commit()

            assert cursor.rowcount == 3

            # Verify specific IDs deleted
            for id_val in selected_ids:
                result = conn.execute(
                    "SELECT COUNT(*) FROM scraped_data WHERE id = ?",
                    (id_val,)
                ).fetchone()[0]
                assert result == 0


class TestSelectionUI:
    """Test UI-related selection features."""

    def test_visual_indicator_logic(self):
        """Test visual indicator logic for bulk selection."""
        selected_ids = {1, 3, 5}
        single_selected_id = None  # For compatibility with single selection

        # Test ID display logic
        test_ids = [1, 2, 3, 4, 5]
        displays = []

        for test_id in test_ids:
            if test_id in selected_ids:
                display = f"[✓] {test_id}"
            elif test_id == single_selected_id:
                display = f"*{test_id}"
            else:
                display = str(test_id)
            displays.append(display)

        assert displays[0] == "[✓] 1"  # In bulk selection
        assert displays[1] == "2"       # Not selected
        assert displays[2] == "[✓] 3"  # In bulk selection
        assert displays[3] == "4"       # Not selected
        assert displays[4] == "[✓] 5"  # In bulk selection

    def test_status_bar_count(self):
        """Test status bar bulk selection count."""
        selected_ids = {1, 2, 3, 4, 5}
        bulk_selected_count = len(selected_ids)

        assert bulk_selected_count == 5

        # Add more
        selected_ids.add(6)
        bulk_selected_count = len(selected_ids)
        assert bulk_selected_count == 6

        # Remove some
        selected_ids.discard(3)
        selected_ids.discard(4)
        bulk_selected_count = len(selected_ids)
        assert bulk_selected_count == 4


class TestBulkOperationsIntegration:
    """Test integration of bulk operations with database."""

    def test_select_and_delete_workflow(self, temp_db_with_data):
        """Test complete select and delete workflow."""
        # Step 1: Get initial count
        with sqlite3.connect(temp_db_with_data) as conn:
            initial_count = conn.execute("SELECT COUNT(*) FROM scraped_data").fetchone()[0]
            assert initial_count == 10

        # Step 2: Select some IDs
        selected_ids = {1, 2, 3}

        # Step 3: Delete selected
        with sqlite3.connect(temp_db_with_data) as conn:
            placeholders = ','.join('?' * len(selected_ids))
            cursor = conn.execute(
                f"DELETE FROM scraped_data WHERE id IN ({placeholders})",
                list(selected_ids)
            )
            conn.commit()
            assert cursor.rowcount == 3

        # Step 4: Verify new count
        with sqlite3.connect(temp_db_with_data) as conn:
            final_count = conn.execute("SELECT COUNT(*) FROM scraped_data").fetchone()[0]
            assert final_count == 7

    def test_select_filtered_and_delete(self, temp_db_with_data):
        """Test selecting filtered results and bulk deleting."""
        # Simulate filtering by title pattern
        with sqlite3.connect(temp_db_with_data) as conn:
            # Get IDs matching filter
            cursor = conn.execute(
                "SELECT id FROM scraped_data WHERE title LIKE ?",
                ('%Article%',)
            )
            filtered_ids = [row[0] for row in cursor.fetchall()]

            assert len(filtered_ids) == 10  # All match in this case

            # Select first 5
            selected_ids = filtered_ids[:5]

            # Delete selected
            placeholders = ','.join('?' * len(selected_ids))
            cursor = conn.execute(
                f"DELETE FROM scraped_data WHERE id IN ({placeholders})",
                selected_ids
            )
            conn.commit()

            # Verify
            remaining = conn.execute("SELECT COUNT(*) FROM scraped_data").fetchone()[0]
            assert remaining == 5
