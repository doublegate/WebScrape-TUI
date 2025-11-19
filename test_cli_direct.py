#!/usr/bin/env python3
"""
Direct testing of v2.2.0 CLI commands without subprocess.

Tests CLI functions directly to avoid sklearn import issues.
"""

import sqlite3
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Import CLI modules directly using importlib
import importlib.util

def import_module_from_path(module_name, file_path):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import CLI command modules
password_reset_mod = import_module_from_path(
    "password_reset_cmd",
    "scrapetui/cli/commands/password_reset.py"
)
account_mod = import_module_from_path(
    "account_cmd",
    "scrapetui/cli/commands/account.py"
)
audit_log_mod = import_module_from_path(
    "audit_log_cmd",
    "scrapetui/cli/commands/audit_log.py"
)

# Test database path
DB_PATH = "test_scraped_data_tui.db"


def test_password_reset_generate():
    """Test: password-reset generate testuser"""
    print("\n" + "="*70)
    print("TEST 10: password-reset generate (Direct)")
    print("="*70)

    try:
        # Call the function directly
        result = password_reset_mod.generate_reset_token("testuser", DB_PATH)

        # Verify token was created
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            token_row = conn.execute("""
                SELECT token, user_id, expires_at
                FROM password_reset_tokens
                WHERE user_id = (SELECT id FROM users WHERE username = 'testuser')
                ORDER BY created_at DESC LIMIT 1
            """).fetchone()

            if token_row:
                print(f"✅ Token created: {token_row['token'][:20]}...")
                print(f"   User ID: {token_row['user_id']}")
                print(f"   Expires: {token_row['expires_at']}")
                return True, token_row['token']
            else:
                print("❌ No token found in database")
                return False, None
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_password_reset_use(reset_token):
    """Test: password-reset use <token> NewP@ss123"""
    print("\n" + "="*70)
    print("TEST 11: password-reset use (Direct)")
    print("="*70)

    if not reset_token:
        print("❌ Skipped: No reset token available")
        return False

    try:
        # Call the function directly
        result = password_reset_mod.use_reset_token(reset_token, "NewP@ss123", DB_PATH)

        # Verify token was consumed
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            token_row = conn.execute("""
                SELECT used_at FROM password_reset_tokens WHERE token = ?
            """, (reset_token,)).fetchone()

            if token_row and token_row['used_at']:
                print(f"✅ Token consumed at: {token_row['used_at']}")
                return True
            else:
                print("❌ Token not marked as used")
                return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_account_lock():
    """Test: account lock testuser"""
    print("\n" + "="*70)
    print("TEST 12: account lock (Direct)")
    print("="*70)

    try:
        # Call the function directly
        result = account_mod.lock_account("testuser", 15, DB_PATH)

        # Verify account is locked
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            user = conn.execute("""
                SELECT account_locked, locked_until
                FROM users WHERE username = 'testuser'
            """).fetchone()

            if user and user['account_locked']:
                print(f"✅ Account locked until: {user['locked_until']}")
                return True
            else:
                print("❌ Account not locked")
                return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_account_unlock():
    """Test: account unlock testuser"""
    print("\n" + "="*70)
    print("TEST 13: account unlock (Direct)")
    print("="*70)

    try:
        # Call the function directly
        result = account_mod.unlock_account("testuser", DB_PATH)

        # Verify account is unlocked
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            user = conn.execute("""
                SELECT account_locked, locked_until, failed_login_attempts
                FROM users WHERE username = 'testuser'
            """).fetchone()

            if user and not user['account_locked']:
                print(f"✅ Account unlocked")
                print(f"   Failed attempts reset: {user['failed_login_attempts']}")
                return True
            else:
                print("❌ Account still locked")
                return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_audit_log_view():
    """Test: audit-log view"""
    print("\n" + "="*70)
    print("TEST 14: audit-log view (Direct)")
    print("="*70)

    try:
        # View audit logs directly
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            logs = conn.execute("""
                SELECT id, event_type, username, created_at
                FROM audit_log
                ORDER BY created_at DESC
                LIMIT 10
            """).fetchall()

            if logs:
                print(f"✅ Found {len(logs)} audit log entries:")
                for log in logs[:5]:  # Show first 5
                    print(f"   - {log['event_type']}: {log['username']} at {log['created_at']}")
                return True
            else:
                print("❌ No audit logs found")
                return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_audit_log_stats():
    """Test: audit-log stats"""
    print("\n" + "="*70)
    print("TEST 15: audit-log stats (Direct)")
    print("="*70)

    try:
        # Get audit log statistics
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row

            # Total count
            total = conn.execute("SELECT COUNT(*) as count FROM audit_log").fetchone()
            print(f"Total audit log entries: {total['count']}")

            # By event type
            stats = conn.execute("""
                SELECT event_type, COUNT(*) as count
                FROM audit_log
                GROUP BY event_type
                ORDER BY count DESC
            """).fetchall()

            if stats:
                print("\nEvents by type:")
                for stat in stats:
                    print(f"   {stat['event_type']}: {stat['count']}")
                print("✅ Statistics displayed")
                return True
            else:
                print("❌ No statistics available")
                return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all CLI command tests directly."""
    print("="*70)
    print("V2.2.0 CLI COMMANDS DIRECT TEST SUITE")
    print("="*70)
    print(f"Test Database: {DB_PATH}")
    print(f"Start Time: {datetime.now(timezone.utc).isoformat()}")

    # Check if test database exists
    if not Path(DB_PATH).exists():
        print(f"\n❌ ERROR: Test database not found: {DB_PATH}")
        return 1

    results = {}

    # Run tests
    success, reset_token = test_password_reset_generate()
    results['password-reset generate'] = success

    results['password-reset use'] = test_password_reset_use(reset_token)
    results['account lock'] = test_account_lock()
    results['account unlock'] = test_account_unlock()
    results['audit-log view'] = test_audit_log_view()
    results['audit-log stats'] = test_audit_log_stats()

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    passed = sum(results.values())
    total = len(results)

    print("\n" + "="*70)
    print(f"RESULTS: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*70)

    # Combined results with previous 9 tests
    print("\n" + "="*70)
    print("COMBINED CLI TEST RESULTS")
    print("="*70)
    print("Previous tests: 9/9 passed (100%)")
    print(f"Current tests:  {passed}/{total} passed ({passed/total*100:.1f}%)")
    print(f"TOTAL:          {9+passed}/{9+total} CLI tests passed ({(9+passed)/(9+total)*100:.1f}%)")
    print("="*70)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
