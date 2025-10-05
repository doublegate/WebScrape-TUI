#!/usr/bin/env python3
"""User management CLI commands."""

import click
import sys
from getpass import getpass

from ...core.database import get_db_connection, init_db
from ...core.auth import hash_password, db_datetime_now
from ...utils.logging import get_logger

logger = get_logger(__name__)


@click.group()
def user():
    """User management commands."""


@user.command()
@click.option('--username', required=True, help='Username for new user')
@click.option('--role', type=click.Choice(['admin', 'user', 'viewer']), default='user',
              help='User role')
@click.option('--email', help='Email address (optional)')
def create(username, role, email):
    """
    Create a new user.

    Example:
        python -m scrapetui user create --username alice --role user --email alice@example.com
    """
    try:
        init_db()

        # Prompt for password (hidden input)
        password = getpass(f"Password for {username}: ")
        password_confirm = getpass("Confirm password: ")

        if password != password_confirm:
            click.echo("✗ Passwords do not match", err=True)
            sys.exit(1)

        if len(password) < 8:
            click.echo("✗ Password must be at least 8 characters", err=True)
            sys.exit(1)

        # Hash password
        password_hash = hash_password(password)

        with get_db_connection() as conn:
            # Check if username exists
            existing = conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,)
            ).fetchone()

            if existing:
                click.echo(f"✗ Username '{username}' already exists", err=True)
                sys.exit(1)

            # Create user
            cursor = conn.execute("""
                INSERT INTO users (username, password_hash, email, role, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (username, password_hash, email, role, db_datetime_now()))

            user_id = cursor.lastrowid
            conn.commit()

        click.echo(f"✓ User '{username}' created successfully (ID: {user_id}, Role: {role})")

    except Exception as e:
        logger.error(f"User creation failed: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@user.command()
@click.option('--format', 'output_format', type=click.Choice(['text', 'table']), default='table',
              help='Output format')
def list(output_format):
    """
    List all users.

    Example:
        python -m scrapetui user list
    """
    try:
        init_db()

        with get_db_connection() as conn:
            rows = conn.execute("""
                SELECT id, username, email, role, created_at, last_login, is_active
                FROM users
                ORDER BY created_at DESC
            """).fetchall()

        if not rows:
            click.echo("No users found")
            return

        if output_format == 'table':
            # Print header
            click.echo(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Role':<10} {'Active':<8} {'Created':<20}")
            click.echo("-" * 100)

            # Print rows
            for row in rows:
                user_id, username, email, role, created_at, last_login, is_active = row
                active_str = "Yes" if is_active else "No"
                email_str = email or "-"

                click.echo(f"{user_id:<5} {username:<20} {email_str:<30} {role:<10} {active_str:<8} {created_at:<20}")

            click.echo(f"\nTotal: {len(rows)} users")

        else:
            for row in rows:
                user_id, username, email, role, created_at, last_login, is_active = row
                click.echo(f"{user_id}: {username} ({role}) - Active: {is_active}")

    except Exception as e:
        logger.error(f"User listing failed: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@user.command()
@click.option('--username', required=True, help='Username to reset password for')
def reset_password(username):
    """
    Reset a user's password.

    Example:
        python -m scrapetui user reset-password --username alice
    """
    try:
        init_db()

        with get_db_connection() as conn:
            # Check user exists
            row = conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,)
            ).fetchone()

            if not row:
                click.echo(f"✗ User '{username}' not found", err=True)
                sys.exit(1)

            user_id = row[0]

        # Prompt for new password
        password = getpass(f"New password for {username}: ")
        password_confirm = getpass("Confirm password: ")

        if password != password_confirm:
            click.echo("✗ Passwords do not match", err=True)
            sys.exit(1)

        if len(password) < 8:
            click.echo("✗ Password must be at least 8 characters", err=True)
            sys.exit(1)

        # Hash password
        password_hash = hash_password(password)

        with get_db_connection() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (password_hash, user_id)
            )
            conn.commit()

        click.echo(f"✓ Password reset successfully for user '{username}'")

    except Exception as e:
        logger.error(f"Password reset failed: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
