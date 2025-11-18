#!/usr/bin/env python3
"""
Test script for v2.2.0 security features.

This script creates a test database, runs the migration, and tests
the core security functionality.
"""

import sys
import os
import sqlite3
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapetui.core.auth import hash_password, verify_password
from scrapetui.core.password_policy import validate_password, PasswordPolicy
from scrapetui.core.rate_limit import RateLimiter, RateLimitConfig
from scrapetui.core.audit import get_audit_logger, AuditEventType
from scrapetui.core.quotas import get_quota_manager, QuotaType
from scrapetui.core.password_reset import get_password_reset_manager
from scrapetui.core.auth_enhanced import (
    authenticate_user_enhanced,
    create_user_with_policy,
    change_password_with_policy
)


def create_v2_1_0_test_database(db_path: str) -> None:
    """Create a v2.1.0-style database for testing migration."""
    print("\n" + "="*60)
    print("Creating v2.1.0 Test Database")
    print("="*60)

    conn = sqlite3.connect(db_path)

    # Create v2.1.0 schema
    print("  → Creating tables...")

    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            last_login TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE user_sessions (
            id INTEGER PRIMARY KEY,
            session_token TEXT UNIQUE,
            user_id INTEGER,
            created_at TEXT,
            expires_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE scraped_data (
            id INTEGER PRIMARY KEY,
            title TEXT,
            content TEXT,
            url TEXT,
            user_id INTEGER,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE saved_scrapers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            url_pattern TEXT,
            user_id INTEGER,
            is_shared INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE schema_version (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
    """)

    # Insert v2.1.0 version
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT INTO schema_version (version, applied_at)
        VALUES ('2.1.0', ?)
    """, (now,))

    # Create test users
    print("  → Creating test users...")

    admin_hash = hash_password('AdminP@ss123')
    conn.execute("""
        INSERT INTO users (id, username, password_hash, role, is_active, created_at, email)
        VALUES (1, 'admin', ?, 'admin', 1, ?, 'admin@example.com')
    """, (admin_hash, now))

    user_hash = hash_password('UserP@ss123')
    conn.execute("""
        INSERT INTO users (id, username, password_hash, role, is_active, created_at, email)
        VALUES (2, 'testuser', ?, 'user', 1, ?, 'user@example.com')
    """, (user_hash, now))

    # Create test data
    print("  → Creating test data...")

    conn.execute("""
        INSERT INTO scraped_data (title, url, content, user_id, created_at)
        VALUES ('Test Article', 'http://example.com', 'Test content', 1, ?)
    """, (now,))

    conn.commit()
    conn.close()

    print(f"\n✓ Test database created: {db_path}")
    print("  Users created:")
    print("    - admin / AdminP@ss123 (role: admin)")
    print("    - testuser / UserP@ss123 (role: user)")


def run_migration(db_path: str) -> bool:
    """Run v2.2.0 migration."""
    print("\n" + "="*60)
    print("Running v2.2.0 Migration")
    print("="*60 + "\n")

    from scrapetui.database.migrations.v2_2_0 import migrate

    return migrate(db_path, skip_backup=True)


def test_password_policy() -> None:
    """Test password policy validation."""
    print("\n" + "="*60)
    print("Testing Password Policy")
    print("="*60)

    # Test weak password
    print("\n1. Testing weak password:")
    result = validate_password("weak")
    print(f"   Password: 'weak'")
    print(f"   Valid: {result.is_valid}")
    print(f"   Strength: {result.strength_level} ({result.score}/100)")
    print(f"   Errors: {', '.join(result.errors) if result.errors else 'None'}")

    # Test strong password
    print("\n2. Testing strong password:")
    result = validate_password("Str0ng!P@ssw0rd2024")
    print(f"   Password: 'Str0ng!P@ssw0rd2024'")
    print(f"   Valid: {result.is_valid}")
    print(f"   Strength: {result.strength_level} ({result.score}/100)")
    print(f"   Errors: {', '.join(result.errors) if result.errors else 'None'}")


def test_rate_limiting(db_path: str) -> None:
    """Test rate limiting functionality."""
    print("\n" + "="*60)
    print("Testing Rate Limiting")
    print("="*60)

    config = RateLimitConfig(max_attempts=3, lockout_duration_minutes=5)
    limiter = RateLimiter(db_path, config)

    username = "testuser"

    print(f"\n1. Testing failed login attempts for '{username}':")
    for i in range(4):
        result = limiter.check_rate_limit(username)
        print(f"   Attempt {i+1}: Allowed={result.allowed}, Remaining={result.attempts_remaining}")

        if result.allowed:
            limiter.record_login_attempt(username, success=False)


def test_audit_logging(db_path: str) -> None:
    """Test audit logging."""
    print("\n" + "="*60)
    print("Testing Audit Logging")
    print("="*60)

    logger = get_audit_logger(db_path)

    print("\n1. Logging test events:")

    # Log a login success
    event_id = logger.log(
        AuditEventType.LOGIN_SUCCESS,
        user_id=1,
        username="admin",
        ip_address="127.0.0.1",
        event_data={"browser": "Test Browser"}
    )
    print(f"   ✓ Logged LOGIN_SUCCESS (ID: {event_id})")

    # Log a password change
    event_id = logger.log(
        AuditEventType.PASSWORD_CHANGED,
        user_id=1,
        username="admin",
        ip_address="127.0.0.1"
    )
    print(f"   ✓ Logged PASSWORD_CHANGED (ID: {event_id})")

    # Get recent events
    print("\n2. Retrieving recent events:")
    events = logger.get_events(limit=5)
    for event in events:
        print(f"   - {event['event_type']} by {event['username']} at {event['created_at'][:19]}")


def test_quotas(db_path: str) -> None:
    """Test quota management."""
    print("\n" + "="*60)
    print("Testing Quotas")
    print("="*60)

    quota_mgr = get_quota_manager(db_path)

    # Get quota status for test user
    print("\n1. Checking quotas for testuser (ID: 2):")
    quotas = quota_mgr.get_all_quotas(2)

    for quota_type, status in quotas.items():
        if status.quota_limit == -1:
            print(f"   {quota_type.title()}: Unlimited")
        else:
            print(f"   {quota_type.title()}: {status.current_usage}/{status.quota_limit} "
                  f"({status.percentage_used:.1f}%)")

    # Check quota availability
    print("\n2. Testing quota checks:")
    can_create = quota_mgr.check_quota(2, QuotaType.ARTICLES)
    print(f"   Can create article: {can_create}")


def test_password_reset(db_path: str) -> None:
    """Test password reset system."""
    print("\n" + "="*60)
    print("Testing Password Reset")
    print("="*60)

    reset_mgr = get_password_reset_manager(db_path)

    print("\n1. Generating reset token for testuser (ID: 2):")
    token, expires_at = reset_mgr.generate_reset_token(2, created_by=1)
    print(f"   Token: {token[:16]}...{token[-16:]}")
    print(f"   Expires: {expires_at}")

    print("\n2. Validating token:")
    is_valid, user_id = reset_mgr.validate_token(token)
    print(f"   Valid: {is_valid}, User ID: {user_id}")


def test_enhanced_auth(db_path: str) -> None:
    """Test enhanced authentication."""
    print("\n" + "="*60)
    print("Testing Enhanced Authentication")
    print("="*60)

    # Test successful login
    print("\n1. Testing successful login:")
    user_id, token, message = authenticate_user_enhanced(
        "admin",
        "AdminP@ss123",
        db_path=db_path,
        ip_address="127.0.0.1",
        user_agent="TestAgent/1.0"
    )
    print(f"   Result: {message}")
    print(f"   User ID: {user_id}")
    print(f"   Token: {token[:16] if token else None}...{token[-16:] if token else None}")

    # Test failed login
    print("\n2. Testing failed login:")
    user_id, token, message = authenticate_user_enhanced(
        "admin",
        "WrongPassword",
        db_path=db_path,
        ip_address="127.0.0.1"
    )
    print(f"   Result: {message}")
    print(f"   User ID: {user_id}")


def test_user_creation(db_path: str) -> None:
    """Test user creation with password policy."""
    print("\n" + "="*60)
    print("Testing User Creation")
    print("="*60)

    # Test with weak password
    print("\n1. Creating user with weak password:")
    user_id, message = create_user_with_policy(
        "weakuser",
        "weak",
        db_path=db_path,
        created_by=1
    )
    print(f"   Result: {message}")
    print(f"   User ID: {user_id}")

    # Test with strong password
    print("\n2. Creating user with strong password:")
    user_id, message = create_user_with_policy(
        "newuser",
        "N3wUs3r!P@ssw0rd",
        email="newuser@example.com",
        db_path=db_path,
        created_by=1
    )
    print(f"   Result: {message}")
    print(f"   User ID: {user_id}")


def run_all_tests():
    """Run all security feature tests."""
    db_path = "test_v2.2.0.db"

    try:
        # Clean up old test database
        if os.path.exists(db_path):
            os.remove(db_path)
            print("✓ Removed old test database")

        # Create v2.1.0 database
        create_v2_1_0_test_database(db_path)

        # Run migration
        success = run_migration(db_path)

        if not success:
            print("\n✗ Migration failed!")
            return False

        # Run tests
        test_password_policy()
        test_rate_limiting(db_path)
        test_audit_logging(db_path)
        test_quotas(db_path)
        test_password_reset(db_path)
        test_enhanced_auth(db_path)
        test_user_creation(db_path)

        print("\n" + "="*60)
        print("✓ All Tests Completed Successfully!")
        print("="*60)

        print(f"\n📊 Test Database: {db_path}")
        print("   You can inspect the database with:")
        print(f"   sqlite3 {db_path}")

        return True

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
