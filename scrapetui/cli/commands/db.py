#!/usr/bin/env python3
"""Database management CLI commands."""

import click
import sys
import shutil

from ...core.database import init_db, check_database_exists, get_db_path
from ...utils.logging import get_logger

logger = get_logger(__name__)


@click.group()
def db():
    """Database management commands."""


@db.command()
def init():
    """
    Initialize database schema.

    Example:
        python -m scrapetui db init
    """
    try:
        if check_database_exists():
            click.echo("⚠ Database already exists")
            if not click.confirm("Reinitialize database? (This will not delete existing data)"):
                return

        click.echo("Initializing database...")
        init_db()

        click.echo("✓ Database initialized successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@db.command()
@click.option('--output', required=True, type=click.Path(), help='Backup file path')
def backup(output):
    """
    Backup database to file.

    Example:
        python -m scrapetui db backup --output backup.db
    """
    try:
        db_path = get_db_path()

        if not check_database_exists():
            click.echo("✗ Database does not exist", err=True)
            sys.exit(1)

        click.echo(f"Backing up database to {output}...")

        # Copy database file
        shutil.copy2(db_path, output)

        click.echo(f"✓ Database backed up successfully to {output}")

    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@db.command()
@click.option('--input', 'input_file', required=True, type=click.Path(exists=True),
              help='Backup file to restore')
def restore(input_file):
    """
    Restore database from backup file.

    Example:
        python -m scrapetui db restore --input backup.db
    """
    try:
        db_path = get_db_path()

        if check_database_exists():
            click.echo("⚠ Existing database will be overwritten")
            if not click.confirm("Continue with restore?"):
                return

            # Backup current database
            backup_path = f"{db_path}.pre-restore-backup"
            shutil.copy2(db_path, backup_path)
            click.echo(f"Current database backed up to {backup_path}")

        click.echo(f"Restoring database from {input_file}...")

        # Copy backup file to database location
        shutil.copy2(input_file, db_path)

        click.echo(f"✓ Database restored successfully from {input_file}")

    except Exception as e:
        logger.error(f"Database restore failed: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@db.command()
def migrate():
    """
    Run database migrations (if any).

    Example:
        python -m scrapetui db migrate
    """
    try:
        click.echo("Checking for database migrations...")

        # Ensure database exists
        if not check_database_exists():
            click.echo("✗ Database does not exist. Run 'db init' first.", err=True)
            sys.exit(1)

        # Run init_db which handles migrations
        init_db()

        click.echo("✓ Database migrations complete")

    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
