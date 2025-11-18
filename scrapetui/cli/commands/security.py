"""
CLI commands for v2.2.0 security features.

Provides command-line access to password reset, account management,
audit logs, and quota administration.
"""

import click
from datetime import datetime, timedelta, timezone
import json
from typing import Optional

from ...core.password_reset import get_password_reset_manager
from ...core.rate_limit import get_rate_limiter
from ...core.audit import get_audit_logger, AuditEventType
from ...core.quotas import get_quota_manager, QuotaType
from ...core.database import get_db_connection


@click.group(name='security')
def security_group():
    """Security and administrative commands (v2.2.0+)."""
    pass


# ============================================================================
# Password Reset Commands
# ============================================================================

@security_group.group(name='password')
def password_group():
    """Password management commands."""
    pass


@password_group.command(name='reset-token')
@click.argument('username')
@click.option('--admin-id', type=int, help='Admin user ID performing reset')
def generate_reset_token(username: str, admin_id: Optional[int]):
    """
    Generate password reset token for user.

    Example:
        scrapetui-cli security password reset-token john --admin-id 1
    """
    try:
        # Get user_id from username
        with get_db_connection() as conn:
            user = conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,)
            ).fetchone()

            if not user:
                click.echo(f"Error: User '{username}' not found", err=True)
                return

            user_id = user[0]

        # Generate token
        reset_mgr = get_password_reset_manager()
        token, expires_at = reset_mgr.generate_reset_token(
            user_id,
            created_by=admin_id
        )

        click.echo(f"Password reset token generated for user: {username}")
        click.echo(f"Token: {token}")
        click.echo(f"Expires: {expires_at}")
        click.echo("\nProvide this token to the user to reset their password.")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


@password_group.command(name='force-change')
@click.argument('username')
def force_password_change(username: str):
    """
    Force user to change password on next login.

    Example:
        scrapetui-cli security password force-change john
    """
    try:
        with get_db_connection() as conn:
            result = conn.execute("""
                UPDATE users
                SET force_password_change = 1
                WHERE username = ?
            """, (username,))

            if result.rowcount == 0:
                click.echo(f"Error: User '{username}' not found", err=True)
                return

            conn.commit()

        click.echo(f"User '{username}' will be required to change password on next login")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


# ============================================================================
# Account Management Commands
# ============================================================================

@security_group.group(name='account')
def account_group():
    """Account management commands."""
    pass


@account_group.command(name='lock')
@click.argument('username')
def lock_account(username: str):
    """
    Lock user account (requires manual unlock).

    Example:
        scrapetui-cli security account lock john
    """
    try:
        limiter = get_rate_limiter()
        limiter.lock_account(username, admin_lock=True)
        click.echo(f"Account '{username}' has been locked")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


@account_group.command(name='unlock')
@click.argument('username')
def unlock_account(username: str):
    """
    Unlock user account.

    Example:
        scrapetui-cli security account unlock john
    """
    try:
        limiter = get_rate_limiter()
        limiter.unlock_account(username)
        click.echo(f"Account '{username}' has been unlocked")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


@account_group.command(name='status')
@click.argument('username')
def account_status(username: str):
    """
    Show account security status.

    Example:
        scrapetui-cli security account status john
    """
    try:
        with get_db_connection() as conn:
            conn.row_factory = lambda cursor, row: dict(
                zip([col[0] for col in cursor.description], row)
            )

            user = conn.execute("""
                SELECT
                    username,
                    is_active,
                    account_locked,
                    locked_until,
                    failed_login_attempts,
                    last_failed_login,
                    password_changed_at,
                    force_password_change,
                    last_login
                FROM users
                WHERE username = ?
            """, (username,)).fetchone()

            if not user:
                click.echo(f"Error: User '{username}' not found", err=True)
                return

        click.echo(f"\nAccount Status for: {user['username']}")
        click.echo("=" * 50)
        click.echo(f"Active: {'Yes' if user['is_active'] else 'No'}")
        click.echo(f"Locked: {'Yes' if user['account_locked'] else 'No'}")

        if user['locked_until']:
            click.echo(f"Locked Until: {user['locked_until']}")

        click.echo(f"Failed Login Attempts: {user['failed_login_attempts'] or 0}")

        if user['last_failed_login']:
            click.echo(f"Last Failed Login: {user['last_failed_login']}")

        if user['password_changed_at']:
            click.echo(f"Password Last Changed: {user['password_changed_at']}")

        click.echo(f"Force Password Change: {'Yes' if user['force_password_change'] else 'No'}")

        if user['last_login']:
            click.echo(f"Last Login: {user['last_login']}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


# ============================================================================
# Audit Log Commands
# ============================================================================

@security_group.group(name='audit')
def audit_group():
    """Audit log commands."""
    pass


@audit_group.command(name='view')
@click.option('--user', help='Filter by username')
@click.option('--event-type', help='Filter by event type')
@click.option('--since', help='Show events since date (YYYY-MM-DD)')
@click.option('--limit', default=50, help='Maximum number of events to show')
@click.option('--export', help='Export to JSON file')
def view_audit_log(
    user: Optional[str],
    event_type: Optional[str],
    since: Optional[str],
    limit: int,
    export: Optional[str]
):
    """
    View audit log entries.

    Example:
        scrapetui-cli security audit view --user john --limit 10
        scrapetui-cli security audit view --event-type login_failure --since 2025-11-01
        scrapetui-cli security audit view --export audit-log.json
    """
    try:
        logger = get_audit_logger()

        # Parse filters
        user_id = None
        if user:
            with get_db_connection() as conn:
                result = conn.execute(
                    "SELECT id FROM users WHERE username = ?",
                    (user,)
                ).fetchone()
                if result:
                    user_id = result[0]

        event_type_enum = None
        if event_type:
            try:
                event_type_enum = AuditEventType(event_type)
            except ValueError:
                click.echo(f"Error: Invalid event type '{event_type}'", err=True)
                click.echo("Valid types: " + ", ".join([e.value for e in AuditEventType]))
                return

        since_iso = None
        if since:
            try:
                since_date = datetime.strptime(since, "%Y-%m-%d")
                since_iso = since_date.isoformat()
            except ValueError:
                click.echo("Error: Invalid date format. Use YYYY-MM-DD", err=True)
                return

        # Get events
        events = logger.get_events(
            user_id=user_id,
            event_type=event_type_enum,
            since=since_iso,
            limit=limit
        )

        if export:
            # Export to JSON
            with open(export, 'w') as f:
                json.dump(events, f, indent=2)
            click.echo(f"Exported {len(events)} events to {export}")
        else:
            # Display events
            if not events:
                click.echo("No events found matching criteria")
                return

            click.echo(f"\nShowing {len(events)} audit log entries:")
            click.echo("=" * 80)

            for event in events:
                click.echo(f"\nEvent ID: {event['id']}")
                click.echo(f"Type: {event['event_type']}")
                click.echo(f"User: {event['username'] or 'N/A'} (ID: {event['user_id'] or 'N/A'})")
                click.echo(f"Time: {event['created_at']}")

                if event.get('ip_address'):
                    click.echo(f"IP Address: {event['ip_address']}")

                if event.get('event_data'):
                    click.echo(f"Data: {json.dumps(event['event_data'], indent=2)}")

                click.echo("-" * 80)

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


@audit_group.command(name='stats')
def audit_stats():
    """
    Show audit log statistics.

    Example:
        scrapetui-cli security audit stats
    """
    try:
        logger = get_audit_logger()
        stats = logger.get_statistics()

        click.echo("\nAudit Log Statistics")
        click.echo("=" * 50)
        click.echo(f"Total Events: {stats['total_events']}")
        click.echo(f"Last 24 Hours: {stats['last_24h']}")

        if stats['events_by_type']:
            click.echo("\nTop Event Types:")
            for event in stats['events_by_type']:
                click.echo(f"  {event['event_type']}: {event['count']}")

        if stats['events_by_user']:
            click.echo("\nTop Users:")
            for user in stats['events_by_user']:
                username = user['username'] or 'Unknown'
                click.echo(f"  {username}: {user['count']}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


@audit_group.command(name='cleanup')
@click.option('--days', default=90, help='Remove events older than N days')
@click.option('--confirm', is_flag=True, help='Confirm deletion')
def cleanup_audit_log(days: int, confirm: bool):
    """
    Clean up old audit log entries.

    Example:
        scrapetui-cli security audit cleanup --days 90 --confirm
    """
    if not confirm:
        click.echo("Warning: This will permanently delete old audit log entries")
        click.echo(f"Run with --confirm to delete events older than {days} days")
        return

    try:
        logger = get_audit_logger()
        deleted = logger.cleanup_old_logs(retention_days=days)
        click.echo(f"Deleted {deleted} audit log entries older than {days} days")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


# ============================================================================
# Quota Management Commands
# ============================================================================

@security_group.group(name='quota')
def quota_group():
    """User quota management commands."""
    pass


@quota_group.command(name='show')
@click.argument('username')
def show_quota(username: str):
    """
    Show quota status for user.

    Example:
        scrapetui-cli security quota show john
    """
    try:
        with get_db_connection() as conn:
            user = conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,)
            ).fetchone()

            if not user:
                click.echo(f"Error: User '{username}' not found", err=True)
                return

            user_id = user[0]

        quota_mgr = get_quota_manager()
        quotas = quota_mgr.get_all_quotas(user_id)

        click.echo(f"\nQuota Status for: {username}")
        click.echo("=" * 50)

        for quota_type, status in quotas.items():
            click.echo(f"\n{quota_type.title()}:")
            if status.quota_limit == -1:
                click.echo("  Unlimited (admin user)")
            else:
                click.echo(f"  Used: {status.current_usage}")
                click.echo(f"  Limit: {status.quota_limit}")
                click.echo(f"  Remaining: {status.remaining}")
                click.echo(f"  Usage: {status.percentage_used:.1f}%")
                click.echo(f"  Status: {'⚠️ EXCEEDED' if status.exceeded else '✓ OK'}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


@quota_group.command(name='set')
@click.argument('username')
@click.option('--articles', type=int, help='Article quota limit')
@click.option('--scrapers', type=int, help='Scraper profile quota limit')
@click.option('--admin-id', type=int, help='Admin user ID setting quota')
def set_quota(
    username: str,
    articles: Optional[int],
    scrapers: Optional[int],
    admin_id: Optional[int]
):
    """
    Set quota limits for user.

    Example:
        scrapetui-cli security quota set john --articles 20000 --scrapers 200
    """
    if articles is None and scrapers is None:
        click.echo("Error: Specify at least --articles or --scrapers", err=True)
        return

    try:
        with get_db_connection() as conn:
            user = conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,)
            ).fetchone()

            if not user:
                click.echo(f"Error: User '{username}' not found", err=True)
                return

            user_id = user[0]

        quota_mgr = get_quota_manager()
        quota_mgr.set_user_quota(
            user_id,
            article_quota=articles,
            scraper_quota=scrapers,
            set_by=admin_id
        )

        updates = []
        if articles is not None:
            updates.append(f"articles={articles}")
        if scrapers is not None:
            updates.append(f"scrapers={scrapers}")

        click.echo(f"Updated quotas for '{username}': {', '.join(updates)}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


@quota_group.command(name='summary')
def quota_summary():
    """
    Show system-wide quota usage summary.

    Example:
        scrapetui-cli security quota summary
    """
    try:
        quota_mgr = get_quota_manager()
        summary = quota_mgr.get_quota_summary()

        click.echo("\nSystem Quota Summary")
        click.echo("=" * 50)

        # Articles
        near_limit = summary['articles']['near_limit']
        exceeded = summary['articles']['exceeded']

        click.echo(f"\nArticles:")
        click.echo(f"  Users near limit (>80%): {len(near_limit)}")
        click.echo(f"  Users exceeded: {len(exceeded)}")

        if exceeded:
            click.echo("\n  Exceeded users:")
            for user in exceeded:
                click.echo(f"    {user['username']}: {user['usage']}/{user['article_quota']}")

        # Scrapers
        near_limit = summary['scrapers']['near_limit']
        exceeded = summary['scrapers']['exceeded']

        click.echo(f"\nScraper Profiles:")
        click.echo(f"  Users near limit (>80%): {len(near_limit)}")
        click.echo(f"  Users exceeded: {len(exceeded)}")

        if exceeded:
            click.echo("\n  Exceeded users:")
            for user in exceeded:
                click.echo(f"    {user['username']}: {user['usage']}/{user['scraper_quota']}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
