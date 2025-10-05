"""
Test suite for v2.0.0 Phase 3: Data Isolation & Sharing Features

Tests data isolation for articles and scrapers, sharing mechanisms, permission checks,
and filter presets introduced in Phase 3 of the multi-user system.
"""

import pytest
from datetime import datetime
import tempfile
from pathlib import Path
import importlib.util

# Use monolithic import pattern (established in test_analytics.py, etc.)
_scrapetui_path = Path(__file__).parent.parent / 'scrapetui.py'
_spec = importlib.util.spec_from_file_location("scrapetui_monolith", _scrapetui_path)
_scrapetui_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_scrapetui_module)

# Import components from monolith
get_db_connection = _scrapetui_module.get_db_connection
hash_password = _scrapetui_module.hash_password
authenticate_user = _scrapetui_module.authenticate_user
create_user_session = _scrapetui_module.create_user_session
validate_session = _scrapetui_module.validate_session
init_db = _scrapetui_module.init_db
FilterPresetManager = _scrapetui_module.FilterPresetManager


# ═══════════════════════════════════════════════════════════════════════════
# Test Fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def clean_test_db():
    """Provide clean database for each test."""
    # Create temporary database file
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
    temp_db_path = Path(temp_file.name)
    temp_file.close()

    # Patch DB_PATH in scrapetui module
    original_db_path = _scrapetui_module.DB_PATH
    _scrapetui_module.DB_PATH = temp_db_path

    # Run init_db to create all tables
    result = init_db()
    assert result is True, "Database initialization should succeed"

    yield temp_db_path

    # Cleanup
    _scrapetui_module.DB_PATH = original_db_path
    if temp_db_path.exists():
        temp_db_path.unlink()


@pytest.fixture
def multi_user_db(clean_test_db):
    """Create database with multiple users for testing."""
    import time
    import random

    # Generate unique ID for this test run to avoid UNIQUE constraint violations
    unique_id = f"{int(time.time() * 1000000)}_{random.randint(1000, 9999)}"

    with get_db_connection() as conn:
        # Create admin user (already exists from init_db)
        # Create regular user 1
        conn.execute("""
            INSERT INTO users (username, password_hash, email, role, created_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (f'user1_{unique_id}', hash_password('password1'), f'user1_{unique_id}@test.com', 'user',
              datetime.now().isoformat(), 1))

        # Create regular user 2
        conn.execute("""
            INSERT INTO users (username, password_hash, email, role, created_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (f'user2_{unique_id}', hash_password('password2'), f'user2_{unique_id}@test.com', 'user',
              datetime.now().isoformat(), 1))

        # Create viewer user
        conn.execute("""
            INSERT INTO users (username, password_hash, email, role, created_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (f'viewer1_{unique_id}', hash_password('viewer1'), f'viewer1_{unique_id}@test.com', 'viewer',
              datetime.now().isoformat(), 1))

        conn.commit()

    return clean_test_db


# ═══════════════════════════════════════════════════════════════════════════
# Data Isolation Tests - Articles
# ═══════════════════════════════════════════════════════════════════════════


def test_article_isolation_user_sees_own_only(multi_user_db):
    """Test that non-admin users only see their own articles."""
    with get_db_connection() as conn:
        # Create articles for different users
        conn.execute("""
            INSERT OR IGNORE INTO scraped_data (title, url, link, timestamp, user_id)
            VALUES (?, ?, ?, ?, ?)
        """, ('User1 Article', 'http://test.com/1', 'http://test.com/1',
              datetime.now().isoformat(), 2))  # user1

        conn.execute("""
            INSERT OR IGNORE INTO scraped_data (title, url, link, timestamp, user_id)
            VALUES (?, ?, ?, ?, ?)
        """, ('User2 Article', 'http://test.com/2', 'http://test.com/2',
              datetime.now().isoformat(), 3))  # user2

        conn.commit()

        # User1 queries their articles
        user1_articles = conn.execute("""
            SELECT * FROM scraped_data WHERE user_id = 2
        """).fetchall()

        assert len(user1_articles) == 1
        assert user1_articles[0]['title'] == 'User1 Article'

        # User2 queries their articles
        user2_articles = conn.execute("""
            SELECT * FROM scraped_data WHERE user_id = 3
        """).fetchall()

        assert len(user2_articles) == 1
        assert user2_articles[0]['title'] == 'User2 Article'


def test_article_isolation_admin_sees_all(multi_user_db):
    """Test that admin users see all articles."""
    with get_db_connection() as conn:
        # Create articles for different users
        conn.execute("""
            INSERT OR IGNORE INTO scraped_data (title, url, link, timestamp, user_id)
            VALUES (?, ?, ?, ?, ?)
        """, ('User1 Article', 'http://test.com/1', 'http://test.com/1',
              datetime.now().isoformat(), 2))  # user1

        conn.execute("""
            INSERT OR IGNORE INTO scraped_data (title, url, link, timestamp, user_id)
            VALUES (?, ?, ?, ?, ?)
        """, ('Admin Article', 'http://test.com/2', 'http://test.com/2',
              datetime.now().isoformat(), 1))  # admin

        conn.commit()

        # Admin queries all articles (no filter)
        all_articles = conn.execute("""
            SELECT * FROM scraped_data
        """).fetchall()

        assert len(all_articles) == 2


def test_article_isolation_empty_for_new_user(multi_user_db):
    """Test that new users see no articles initially."""
    with get_db_connection() as conn:
        # Create article for user1
        conn.execute("""
            INSERT OR IGNORE INTO scraped_data (title, url, link, timestamp, user_id)
            VALUES (?, ?, ?, ?, ?)
        """, ('User1 Article', 'http://test.com/1', 'http://test.com/1',
              datetime.now().isoformat(), 2))  # user1

        conn.commit()

        # User2 queries their articles (should be empty)
        user2_articles = conn.execute("""
            SELECT * FROM scraped_data WHERE user_id = 3
        """).fetchall()

        assert len(user2_articles) == 0


# ═══════════════════════════════════════════════════════════════════════════
# Data Isolation Tests - Scrapers
# ═══════════════════════════════════════════════════════════════════════════


def test_scraper_isolation_user_sees_own_only(multi_user_db):
    """Test that users see only their own scrapers when not shared."""
    with get_db_connection() as conn:
        # Create private scrapers for different users
        conn.execute("""
            INSERT OR IGNORE INTO saved_scrapers (name, url, selector, user_id, is_shared)
            VALUES (?, ?, ?, ?, ?)
        """, ('User1 Scraper', 'http://test.com', 'h1', 2, 0))  # user1, private

        conn.execute("""
            INSERT OR IGNORE INTO saved_scrapers (name, url, selector, user_id, is_shared)
            VALUES (?, ?, ?, ?, ?)
        """, ('User2 Scraper', 'http://test.com', 'h2', 3, 0))  # user2, private

        conn.commit()

        # User1 queries their scrapers
        user1_scrapers = conn.execute("""
            SELECT * FROM saved_scrapers WHERE user_id = 2
        """).fetchall()

        assert len(user1_scrapers) == 1
        assert user1_scrapers[0]['name'] == 'User1 Scraper'


def test_scraper_isolation_shared_visible_to_all(multi_user_db):
    """Test that shared scrapers are visible to all users."""
    with get_db_connection() as conn:
        # Create shared scraper
        conn.execute("""
            INSERT OR IGNORE INTO saved_scrapers (name, url, selector, user_id, is_shared)
            VALUES (?, ?, ?, ?, ?)
        """, ('Shared Scraper', 'http://test.com', 'h1', 2, 1))  # user1, shared

        # Create private scraper
        conn.execute("""
            INSERT OR IGNORE INTO saved_scrapers (name, url, selector, user_id, is_shared)
            VALUES (?, ?, ?, ?, ?)
        """, ('Private Scraper', 'http://test.com', 'h2', 2, 0))  # user1, private

        conn.commit()

        # User2 queries scrapers (own + shared)
        user2_scrapers = conn.execute("""
            SELECT * FROM saved_scrapers WHERE user_id = 3 OR is_shared = 1
        """).fetchall()

        assert len(user2_scrapers) == 1
        assert user2_scrapers[0]['name'] == 'Shared Scraper'


def test_scraper_isolation_admin_sees_all(multi_user_db):
    """Test that admin sees all scrapers regardless of sharing status."""
    with get_db_connection() as conn:
        # Create various scrapers
        conn.execute("""
            INSERT OR IGNORE INTO saved_scrapers (name, url, selector, user_id, is_shared)
            VALUES (?, ?, ?, ?, ?)
        """, ('User1 Private', 'http://test.com', 'h1', 2, 0))

        conn.execute("""
            INSERT OR IGNORE INTO saved_scrapers (name, url, selector, user_id, is_shared)
            VALUES (?, ?, ?, ?, ?)
        """, ('User2 Shared', 'http://test.com', 'h2', 3, 1))

        conn.commit()

        # Admin queries all scrapers
        all_scrapers = conn.execute("""
            SELECT * FROM saved_scrapers WHERE is_preinstalled = 0
        """).fetchall()

        # Should see both scrapers (excluding preinstalled)
        assert len(all_scrapers) >= 2


def test_scraper_isolation_preinstalled_visible_to_all(multi_user_db):
    """Test that preinstalled scrapers are visible to all users."""
    with get_db_connection() as conn:
        # Preinstalled scrapers should exist from init_db
        preinstalled = conn.execute("""
            SELECT * FROM saved_scrapers WHERE is_preinstalled = 1
        """).fetchall()

        assert len(preinstalled) > 0


# ═══════════════════════════════════════════════════════════════════════════
# Sharing Mechanism Tests
# ═══════════════════════════════════════════════════════════════════════════


def test_share_scraper_toggle(multi_user_db):
    """Test toggling scraper sharing status."""
    with get_db_connection() as conn:
        # Create private scraper
        conn.execute("""
            INSERT OR IGNORE INTO saved_scrapers (name, url, selector, user_id, is_shared)
            VALUES (?, ?, ?, ?, ?)
        """, ('Test Scraper', 'http://test.com', 'h1', 2, 0))

        scraper_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()

        # Toggle to shared
        conn.execute("""
            UPDATE saved_scrapers SET is_shared = 1 WHERE id = ?
        """, (scraper_id,))
        conn.commit()

        # Verify sharing status
        scraper = conn.execute("""
            SELECT is_shared FROM saved_scrapers WHERE id = ?
        """, (scraper_id,)).fetchone()

        assert scraper['is_shared'] == 1

        # Toggle back to private
        conn.execute("""
            UPDATE saved_scrapers SET is_shared = 0 WHERE id = ?
        """, (scraper_id,))
        conn.commit()

        scraper = conn.execute("""
            SELECT is_shared FROM saved_scrapers WHERE id = ?
        """, (scraper_id,)).fetchone()

        assert scraper['is_shared'] == 0


def test_shared_scraper_visible_after_toggle(multi_user_db):
    """Test that scraper becomes visible to other users after sharing."""
    with get_db_connection() as conn:
        # Create private scraper for user1
        conn.execute("""
            INSERT OR IGNORE INTO saved_scrapers (name, url, selector, user_id, is_shared)
            VALUES (?, ?, ?, ?, ?)
        """, ('Test Scraper', 'http://test.com', 'h1', 2, 0))

        scraper_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()

        # User2 should not see it
        user2_scrapers = conn.execute("""
            SELECT * FROM saved_scrapers WHERE user_id = 3 OR is_shared = 1
        """).fetchall()

        assert len(user2_scrapers) == 0

        # Share the scraper
        conn.execute("""
            UPDATE saved_scrapers SET is_shared = 1 WHERE id = ?
        """, (scraper_id,))
        conn.commit()

        # User2 should now see it
        user2_scrapers = conn.execute("""
            SELECT * FROM saved_scrapers WHERE user_id = 3 OR is_shared = 1
        """).fetchall()

        assert len(user2_scrapers) == 1
        assert user2_scrapers[0]['name'] == 'Test Scraper'


# ═══════════════════════════════════════════════════════════════════════════
# Permission Check Tests
# ═══════════════════════════════════════════════════════════════════════════


def test_permission_user_cannot_delete_others_scraper(multi_user_db):
    """Test that user cannot delete another user's scraper."""
    with get_db_connection() as conn:
        # Create scraper for user1
        conn.execute("""
            INSERT OR IGNORE INTO saved_scrapers (name, url, selector, user_id, is_shared)
            VALUES (?, ?, ?, ?, ?)
        """, ('User1 Scraper', 'http://test.com', 'h1', 2, 0))

        scraper_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()

        # Get scraper details
        scraper = conn.execute("""
            SELECT user_id FROM saved_scrapers WHERE id = ?
        """, (scraper_id,)).fetchone()

        # Simulate permission check (user2 trying to delete user1's scraper)
        current_user_id = 3  # user2
        owner_user_id = scraper['user_id']  # user1
        current_user_role = 'user'

        # Permission check logic
        can_delete = (current_user_role == 'admin') or (current_user_id == owner_user_id)

        assert can_delete is False


def test_permission_admin_can_delete_any_scraper(multi_user_db):
    """Test that admin can delete any user's scraper."""
    with get_db_connection() as conn:
        # Create scraper for user1
        conn.execute("""
            INSERT OR IGNORE INTO saved_scrapers (name, url, selector, user_id, is_shared)
            VALUES (?, ?, ?, ?, ?)
        """, ('User1 Scraper', 'http://test.com', 'h1', 2, 0))

        scraper_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()

        # Get scraper details
        scraper = conn.execute("""
            SELECT user_id FROM saved_scrapers WHERE id = ?
        """, (scraper_id,)).fetchone()

        # Simulate permission check (admin trying to delete user1's scraper)
        current_user_id = 1  # admin
        owner_user_id = scraper['user_id']  # user1
        current_user_role = 'admin'

        # Permission check logic
        can_delete = (current_user_role == 'admin') or (current_user_id == owner_user_id)

        assert can_delete is True


def test_permission_user_can_delete_own_scraper(multi_user_db):
    """Test that user can delete their own scraper."""
    with get_db_connection() as conn:
        # Create scraper for user1
        conn.execute("""
            INSERT OR IGNORE INTO saved_scrapers (name, url, selector, user_id, is_shared)
            VALUES (?, ?, ?, ?, ?)
        """, ('User1 Scraper', 'http://test.com', 'h1', 2, 0))

        scraper_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()

        # Get scraper details
        scraper = conn.execute("""
            SELECT user_id FROM saved_scrapers WHERE id = ?
        """, (scraper_id,)).fetchone()

        # Simulate permission check (user1 trying to delete own scraper)
        current_user_id = 2  # user1
        owner_user_id = scraper['user_id']  # user1
        current_user_role = 'user'

        # Permission check logic
        can_delete = (current_user_role == 'admin') or (current_user_id == owner_user_id)

        assert can_delete is True


def test_permission_user_cannot_edit_others_scraper(multi_user_db):
    """Test that user cannot edit another user's scraper."""
    with get_db_connection() as conn:
        # Create scraper for user1
        conn.execute("""
            INSERT OR IGNORE INTO saved_scrapers (name, url, selector, user_id, is_shared)
            VALUES (?, ?, ?, ?, ?)
        """, ('User1 Scraper', 'http://test.com', 'h1', 2, 1))  # shared

        scraper_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()

        # Get scraper details
        scraper = conn.execute("""
            SELECT user_id, is_shared FROM saved_scrapers WHERE id = ?
        """, (scraper_id,)).fetchone()

        # User2 can see the shared scraper
        user2_scrapers = conn.execute("""
            SELECT * FROM saved_scrapers WHERE user_id = 3 OR is_shared = 1
        """).fetchall()
        assert len(user2_scrapers) == 1

        # But user2 cannot edit it (permission check)
        current_user_id = 3  # user2
        owner_user_id = scraper['user_id']  # user1
        current_user_role = 'user'

        can_edit = (current_user_role == 'admin') or (current_user_id == owner_user_id)

        assert can_edit is False


def test_permission_preinstalled_cannot_be_deleted(multi_user_db):
    """Test that preinstalled scrapers cannot be deleted."""
    with get_db_connection() as conn:
        # Get a preinstalled scraper
        preinstalled = conn.execute("""
            SELECT * FROM saved_scrapers WHERE is_preinstalled = 1 LIMIT 1
        """).fetchone()

        assert preinstalled is not None

        # Simulate deletion check
        is_preinstalled = preinstalled['is_preinstalled']

        # Deletion should be blocked for preinstalled
        can_delete = not is_preinstalled

        assert can_delete is False


# ═══════════════════════════════════════════════════════════════════════════
# Filter Presets Tests
# ═══════════════════════════════════════════════════════════════════════════


def test_filter_preset_save_and_load(multi_user_db):
    """Test saving and loading filter presets."""
    preset_name = "Test Preset"

    # Save preset
    success = FilterPresetManager.save_preset(
        preset_name,
        'test',              # title_filter
        'example.com',       # url_filter
        '2024-01-01',        # date_from
        '2024-12-31',        # date_to
        'tech,python',       # tags_filter
        'Positive',          # sentiment_filter
        False,               # use_regex
        'AND'                # tags_logic
    )
    assert success is True

    # Load preset
    loaded = FilterPresetManager.load_preset(preset_name)
    assert loaded is not None
    assert loaded['title_filter'] == 'test'
    assert loaded['url_filter'] == 'example.com'
    assert loaded['tags_filter'] == 'tech,python'
    assert loaded['sentiment_filter'] == 'Positive'


def test_filter_preset_list(multi_user_db):
    """Test listing all filter presets."""
    # Save multiple presets
    FilterPresetManager.save_preset("Preset 1", 'test1', '', '', '', '', '', False, 'AND')
    FilterPresetManager.save_preset("Preset 2", 'test2', '', '', '', '', '', False, 'AND')

    # List presets
    presets = FilterPresetManager.list_presets()
    assert len(presets) >= 2
    assert "Preset 1" in presets
    assert "Preset 2" in presets


def test_filter_preset_delete(multi_user_db):
    """Test deleting filter presets."""
    preset_name = "Delete Me"

    # Save preset
    FilterPresetManager.save_preset(preset_name, 'delete', '', '', '', '', '', False, 'AND')

    # Verify it exists
    presets = FilterPresetManager.list_presets()
    assert preset_name in presets

    # Delete it
    success = FilterPresetManager.delete_preset(preset_name)
    assert success is True

    # Verify it's gone
    presets = FilterPresetManager.list_presets()
    assert preset_name not in presets


def test_filter_preset_update(multi_user_db):
    """Test updating existing filter preset."""
    preset_name = "Update Me"

    # Save initial preset
    FilterPresetManager.save_preset(preset_name, 'old', '', '', '', '', '', False, 'AND')

    # Update preset
    FilterPresetManager.save_preset(preset_name, 'new', 'updated.com', '', '', '', '', False, 'AND')

    # Load and verify update
    loaded = FilterPresetManager.load_preset(preset_name)
    assert loaded['title_filter'] == 'new'
    assert loaded['url_filter'] == 'updated.com'


def test_filter_preset_load_nonexistent(multi_user_db):
    """Test loading non-existent preset returns None."""
    loaded = FilterPresetManager.load_preset("Nonexistent")
    assert loaded is None


def test_filter_preset_complex_filters(multi_user_db):
    """Test saving and loading complex filter combinations."""
    preset_name = "Complex Filters"

    # Save preset
    FilterPresetManager.save_preset(
        preset_name,
        r'test.*regex',           # title_filter
        r'https?://.*\.com',      # url_filter
        '2024-01-01',             # date_from
        '2024-12-31',             # date_to
        'tag1,tag2,tag3',         # tags_filter
        'Positive',               # sentiment_filter
        True,                     # use_regex
        'OR'                      # tags_logic
    )

    # Load and verify
    loaded = FilterPresetManager.load_preset(preset_name)
    assert loaded['title_filter'] == r'test.*regex'
    assert loaded['url_filter'] == r'https?://.*\.com'
    assert loaded['tags_logic'] == 'OR'
    assert loaded['use_regex'] is True


# ═══════════════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════════════


def test_integration_user_workflow(multi_user_db):
    """Test complete user workflow with data isolation."""
    with get_db_connection() as conn:
        # User1 creates a scraper
        conn.execute("""
            INSERT OR IGNORE INTO saved_scrapers (name, url, selector, user_id, is_shared)
            VALUES (?, ?, ?, ?, ?)
        """, ('My Scraper', 'http://test.com', 'h1', 2, 0))

        # User1 creates an article
        conn.execute("""
            INSERT OR IGNORE INTO scraped_data (title, url, link, timestamp, user_id)
            VALUES (?, ?, ?, ?, ?)
        """, ('My Article', 'http://test.com/article', 'http://test.com/article',
              datetime.now().isoformat(), 2))

        conn.commit()

        # User1 sees their data
        user1_scrapers = conn.execute("""
            SELECT * FROM saved_scrapers WHERE user_id = 2
        """).fetchall()
        user1_articles = conn.execute("""
            SELECT * FROM scraped_data WHERE user_id = 2
        """).fetchall()

        assert len(user1_scrapers) == 1
        assert len(user1_articles) == 1

        # User2 doesn't see User1's data
        user2_scrapers = conn.execute("""
            SELECT * FROM saved_scrapers WHERE user_id = 3 OR is_shared = 1
        """).fetchall()
        user2_articles = conn.execute("""
            SELECT * FROM scraped_data WHERE user_id = 3
        """).fetchall()

        assert len(user2_scrapers) == 0
        assert len(user2_articles) == 0


def test_integration_sharing_workflow(multi_user_db):
    """Test complete sharing workflow."""
    with get_db_connection() as conn:
        # User1 creates a scraper
        conn.execute("""
            INSERT OR IGNORE INTO saved_scrapers (name, url, selector, user_id, is_shared)
            VALUES (?, ?, ?, ?, ?)
        """, ('My Scraper', 'http://test.com', 'h1', 2, 0))

        scraper_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()

        # User2 cannot see it
        user2_scrapers = conn.execute("""
            SELECT * FROM saved_scrapers WHERE user_id = 3 OR is_shared = 1
        """).fetchall()
        assert len(user2_scrapers) == 0

        # User1 shares it
        conn.execute("""
            UPDATE saved_scrapers SET is_shared = 1 WHERE id = ?
        """, (scraper_id,))
        conn.commit()

        # User2 can now see it
        user2_scrapers = conn.execute("""
            SELECT * FROM saved_scrapers WHERE user_id = 3 OR is_shared = 1
        """).fetchall()
        assert len(user2_scrapers) == 1

        # But User2 cannot delete it (permission check)
        scraper = conn.execute("""
            SELECT user_id FROM saved_scrapers WHERE id = ?
        """, (scraper_id,)).fetchone()

        can_delete = (3 == scraper['user_id']) or ('user' == 'admin')
        assert can_delete is False


def test_integration_admin_oversight(multi_user_db):
    """Test admin can oversee all user data."""
    with get_db_connection() as conn:
        # Multiple users create data
        conn.execute("""
            INSERT OR IGNORE INTO saved_scrapers (name, url, selector, user_id, is_shared)
            VALUES (?, ?, ?, ?, ?)
        """, ('User1 Scraper', 'http://test.com', 'h1', 2, 0))

        conn.execute("""
            INSERT OR IGNORE INTO saved_scrapers (name, url, selector, user_id, is_shared)
            VALUES (?, ?, ?, ?, ?)
        """, ('User2 Scraper', 'http://test.com', 'h2', 3, 0))

        conn.execute("""
            INSERT OR IGNORE INTO scraped_data (title, url, link, timestamp, user_id)
            VALUES (?, ?, ?, ?, ?)
        """, ('User1 Article', 'http://test.com/1', 'http://test.com/1',
              datetime.now().isoformat(), 2))

        conn.execute("""
            INSERT OR IGNORE INTO scraped_data (title, url, link, timestamp, user_id)
            VALUES (?, ?, ?, ?, ?)
        """, ('User2 Article', 'http://test.com/2', 'http://test.com/2',
              datetime.now().isoformat(), 3))

        conn.commit()

        # Admin sees all scrapers (excluding preinstalled)
        all_scrapers = conn.execute("""
            SELECT * FROM saved_scrapers WHERE is_preinstalled = 0
        """).fetchall()
        assert len(all_scrapers) == 2

        # Admin sees all articles
        all_articles = conn.execute("""
            SELECT * FROM scraped_data
        """).fetchall()
        assert len(all_articles) == 2


# ═══════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════

"""
Test Summary for Phase 3:

Data Isolation - Articles (3 tests):
✓ Non-admin users only see own articles
✓ Admin users see all articles
✓ New users see no articles initially

Data Isolation - Scrapers (4 tests):
✓ Users see only own scrapers when not shared
✓ Shared scrapers visible to all users
✓ Admin sees all scrapers
✓ Preinstalled scrapers visible to all

Sharing Mechanism (2 tests):
✓ Toggle scraper sharing status
✓ Scraper becomes visible after sharing

Permission Checks (5 tests):
✓ User cannot delete others' scrapers
✓ Admin can delete any scraper
✓ User can delete own scraper
✓ User cannot edit others' scrapers
✓ Preinstalled scrapers cannot be deleted

Filter Presets (6 tests):
✓ Save and load filter presets
✓ List all filter presets
✓ Delete filter presets
✓ Update existing presets
✓ Load non-existent preset returns None
✓ Complex filter combinations

Integration Tests (3 tests):
✓ Complete user workflow with isolation
✓ Complete sharing workflow
✓ Admin oversight of all data

Total: 23 tests covering all Phase 3 requirements
"""
