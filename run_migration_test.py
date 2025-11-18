#!/usr/bin/env python3
"""
Quick database migration test for v2.2.0.

Creates a v2.1.0 database and migrates it to v2.2.0.
"""

import sqlite3
import os
from datetime import datetime, timezone

# Database path
DB_PATH = "test_migration.db"

print("\n" + "="*70)
print("Creating v2.1.0 Test Database for Migration")
print("="*70)

# Remove old database if exists
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"✓ Removed old database: {DB_PATH}")

# Create v2.1.0 schema
conn = sqlite3.connect(DB_PATH)
now = datetime.now(timezone.utc).isoformat()

print("\nCreating v2.1.0 schema...")

# Users table (v2.1.0)
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

# Sessions table
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

# Articles table
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

# Schema version
conn.execute("""
    CREATE TABLE schema_version (
        version TEXT PRIMARY KEY,
        applied_at TEXT NOT NULL
    )
""")

conn.execute("INSERT INTO schema_version (version, applied_at) VALUES ('2.1.0', ?)", (now,))

# Create test user (admin)
conn.execute("""
    INSERT INTO users (id, username, password_hash, role, email, is_active, created_at)
    VALUES (1, 'admin', '$2b$12$test_hash', 'admin', 'admin@example.com', 1, ?)
""", (now,))

# Create test user (regular)
conn.execute("""
    INSERT INTO users (id, username, password_hash, role, email, is_active, created_at)
    VALUES (2, 'testuser', '$2b$12$test_hash', 'user', 'user@example.com', 1, ?)
""", (now,))

# Create test article
conn.execute("""
    INSERT INTO scraped_data (title, url, content, user_id, created_at)
    VALUES ('Test Article', 'http://example.com', 'Test content', 1, ?)
""", (now,))

conn.commit()
conn.close()

print("✓ v2.1.0 database created")
print(f"  - 2 users created (admin, testuser)")
print(f"  - 1 article created")
print(f"  - Schema version: 2.1.0")

# Now run the migration
print("\n" + "="*70)
print("Running v2.2.0 Migration")
print("="*70 + "\n")

# Import migration module directly without package
import importlib.util
spec = importlib.util.spec_from_file_location(
    "v2_2_0",
    "scrapetui/database/migrations/v2_2_0.py"
)
v2_2_0 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2_2_0)

success = v2_2_0.migrate(DB_PATH, skip_backup=True)

if success:
    print("\n" + "="*70)
    print("✅ Migration Successful!")
    print("="*70)

    # Verify migration
    print("\nVerifying migration results...")
    conn = sqlite3.connect(DB_PATH)

    # Check new tables
    cursor = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name IN ('login_attempts', 'password_reset_tokens', 'audit_log')
    """)
    new_tables = [row[0] for row in cursor.fetchall()]
    print(f"\n✓ New tables created: {', '.join(new_tables)}")

    # Check new columns in users table
    cursor = conn.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    new_columns = [c for c in columns if c in ['account_locked', 'locked_until', 'failed_login_attempts',
                                                  'last_failed_login', 'password_changed_at', 'force_password_change',
                                                  'article_quota', 'scraper_quota', 'quota_reset_at']]
    print(f"✓ New columns in users table: {', '.join(new_columns)}")

    # Check admin quota
    cursor = conn.execute("SELECT username, article_quota, scraper_quota FROM users WHERE role='admin'")
    admin = cursor.fetchone()
    print(f"\n✓ Admin quotas set:")
    print(f"  - {admin[0]}: articles={admin[1]}, scrapers={admin[2]} (-1 = unlimited)")

    # Check schema version
    cursor = conn.execute("SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1")
    version = cursor.fetchone()[0]
    print(f"\n✓ Schema version updated: {version}")

    conn.close()

    print("\n" + "="*70)
    print("🎉 Migration Test Complete!")
    print("="*70)
    print(f"\n📊 Test database: {DB_PATH}")
    print("   You can inspect with: sqlite3 test_migration.db")

else:
    print("\n✗ Migration failed!")
    exit(1)
