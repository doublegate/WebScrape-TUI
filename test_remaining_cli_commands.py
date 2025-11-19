#!/usr/bin/env python3
"""
Test remaining v2.2.0 CLI security commands.

Tests the 6 commands not covered in previous testing:
1. password-reset generate
2. password-reset use
3. account lock
4. account unlock
5. audit-log view
6. audit-log stats
"""

import sqlite3
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Test database path
DB_PATH = "test_scraped_data_tui.db"

def run_cli_command(args):
    """Run a CLI command and return output."""
    cmd = ["python", "-m", "scrapetui.cli.main"] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env={"DB_PATH": DB_PATH}
    )
    return result.returncode, result.stdout, result.stderr


def test_password_reset_generate():
    """Test: scrapetui-cli password-reset generate testuser"""
    print("\n" + "="*70)
    print("TEST 10: password-reset generate")
    print("="*70)

    returncode, stdout, stderr = run_cli_command([
        "password-reset", "generate", "testuser"
    ])

    print(f"Return Code: {returncode}")
    print(f"STDOUT:\n{stdout}")
    if stderr:
        print(f"STDERR:\n{stderr}")

    # Verify token was created
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        token = conn.execute("""
            SELECT token, user_id, expires_at
            FROM password_reset_tokens
            WHERE user_id = (SELECT id FROM users WHERE username = 'testuser')
            ORDER BY created_at DESC LIMIT 1
        """).fetchone()

        if token:
            print(f"✅ Token created: {token['token'][:20]}...")
            print(f"   User ID: {token['user_id']}")
            print(f"   Expires: {token['expires_at']}")
            return True, token['token']
        else:
            print("❌ No token found in database")
            return False, None


def test_password_reset_use(reset_token):
    """Test: scrapetui-cli password-reset use <token> NewP@ss123"""
    print("\n" + "="*70)
    print("TEST 11: password-reset use")
    print("="*70)

    if not reset_token:
        print("❌ Skipped: No reset token available")
        return False

    returncode, stdout, stderr = run_cli_command([
        "password-reset", "use", reset_token, "NewP@ss123"
    ])

    print(f"Return Code: {returncode}")
    print(f"STDOUT:\n{stdout}")
    if stderr:
        print(f"STDERR:\n{stderr}")

    # Verify token was consumed
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        token = conn.execute("""
            SELECT used_at FROM password_reset_tokens WHERE token = ?
        """, (reset_token,)).fetchone()

        if token and token['used_at']:
            print(f"✅ Token consumed at: {token['used_at']}")
            return True
        else:
            print("❌ Token not marked as used")
            return False


def test_account_lock():
    """Test: scrapetui-cli account lock testuser"""
    print("\n" + "="*70)
    print("TEST 12: account lock")
    print("="*70)

    returncode, stdout, stderr = run_cli_command([
        "account", "lock", "testuser"
    ])

    print(f"Return Code: {returncode}")
    print(f"STDOUT:\n{stdout}")
    if stderr:
        print(f"STDERR:\n{stderr}")

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


def test_account_unlock():
    """Test: scrapetui-cli account unlock testuser"""
    print("\n" + "="*70)
    print("TEST 13: account unlock")
    print("="*70)

    returncode, stdout, stderr = run_cli_command([
        "account", "unlock", "testuser"
    ])

    print(f"Return Code: {returncode}")
    print(f"STDOUT:\n{stdout}")
    if stderr:
        print(f"STDERR:\n{stderr}")

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


def test_audit_log_view():
    """Test: scrapetui-cli audit-log view --limit 10"""
    print("\n" + "="*70)
    print("TEST 14: audit-log view")
    print("="*70)

    returncode, stdout, stderr = run_cli_command([
        "audit-log", "view", "--limit", "10"
    ])

    print(f"Return Code: {returncode}")
    print(f"STDOUT:\n{stdout}")
    if stderr:
        print(f"STDERR:\n{stderr}")

    # Verify audit logs exist
    with sqlite3.connect(DB_PATH) as conn:
        count = conn.execute("SELECT COUNT(*) as count FROM audit_log").fetchone()['count']
        print(f"✅ Total audit log entries: {count}")
        return count > 0


def test_audit_log_stats():
    """Test: scrapetui-cli audit-log stats"""
    print("\n" + "="*70)
    print("TEST 15: audit-log stats")
    print("="*70)

    returncode, stdout, stderr = run_cli_command([
        "audit-log", "stats"
    ])

    print(f"Return Code: {returncode}")
    print(f"STDOUT:\n{stdout}")
    if stderr:
        print(f"STDERR:\n{stderr}")

    # Check that stats were displayed
    if "event type" in stdout.lower() or "total" in stdout.lower():
        print("✅ Statistics displayed")
        return True
    else:
        print("❌ No statistics in output")
        return False


def main():
    """Run all remaining CLI command tests."""
    print("="*70)
    print("V2.2.0 REMAINING CLI COMMANDS TEST SUITE")
    print("="*70)
    print(f"Test Database: {DB_PATH}")
    print(f"Start Time: {datetime.now(timezone.utc).isoformat()}")

    # Check if test database exists
    if not Path(DB_PATH).exists():
        print(f"\n❌ ERROR: Test database not found: {DB_PATH}")
        print("Please run test_cli_commands.py first to create the test database.")
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

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
