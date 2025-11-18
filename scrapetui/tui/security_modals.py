"""
Enhanced security modals for WebScrape-TUI v2.2.0.

Provides TUI modals for password management, account security,
audit log viewing, and quota management with policy enforcement.
"""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Label, Input, Button, DataTable, Static
from textual.screen import ModalScreen
from typing import Optional, Dict, Any
import json
from datetime import datetime, timezone

from ..core.password_policy import (
    validate_password,
    PasswordPolicy,
    get_strength_color,
    get_strength_emoji
)
from ..core.auth_enhanced import change_password_with_policy
from ..core.password_reset import get_password_reset_manager
from ..core.audit import get_audit_logger, AuditEventType
from ..core.quotas import get_quota_manager, QuotaType
from ..core.database import get_db_connection


class EnhancedChangePasswordModal(ModalScreen[bool]):
    """
    Enhanced password change modal with policy validation.

    Shows real-time password strength feedback and policy requirements.
    """

    DEFAULT_CSS = """
    EnhancedChangePasswordModal {
        align: center middle;
        background: $surface-darken-1;
    }

    EnhancedChangePasswordModal > Vertical {
        width: 70;
        height: auto;
        border: thick $primary;
        background: $panel;
        padding: 2 4;
    }

    EnhancedChangePasswordModal Label {
        margin: 1 0;
    }

    EnhancedChangePasswordModal #pwd-title {
        text-align: center;
        text-style: bold;
        color: $accent;
    }

    EnhancedChangePasswordModal #strength-label {
        text-align: center;
        text-style: bold;
        margin: 1 0;
    }

    EnhancedChangePasswordModal #policy-info {
        color: $text-muted;
        margin: 1 0;
    }

    EnhancedChangePasswordModal Input {
        margin: 1 0;
    }

    EnhancedChangePasswordModal Horizontal {
        width: 100%;
        height: auto;
        align-horizontal: center;
        padding-top: 1;
    }

    EnhancedChangePasswordModal Button {
        margin: 0 1;
    }
    """

    def __init__(
        self,
        user_id: int,
        username: str,
        password_policy: Optional[PasswordPolicy] = None
    ):
        super().__init__()
        self.user_id = user_id
        self.username = username
        self.password_policy = password_policy or PasswordPolicy()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("🔒 Change Password", id="pwd-title")

            # Password policy information
            yield Label(
                f"Requirements: {self.password_policy.min_length}+ chars, "
                "uppercase, lowercase, number, special character",
                id="policy-info"
            )

            yield Input(
                placeholder="Current Password",
                password=True,
                id="current-pwd"
            )
            yield Input(
                placeholder="New Password",
                password=True,
                id="new-pwd"
            )
            yield Input(
                placeholder="Confirm New Password",
                password=True,
                id="confirm-pwd"
            )

            # Strength indicator
            yield Label("", id="strength-label")

            with Horizontal():
                yield Button(
                    "Change Password",
                    variant="primary",
                    id="change-btn"
                )
                yield Button("Cancel", id="cancel-btn")

    def on_mount(self) -> None:
        """Focus current password field."""
        self.query_one("#current-pwd", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Update password strength indicator in real-time."""
        if event.input.id == "new-pwd":
            password = event.value

            if password:
                result = validate_password(
                    password,
                    self.username,
                    self.password_policy
                )

                strength_label = self.query_one("#strength-label", Label)
                emoji = get_strength_emoji(result.strength_level)
                color = get_strength_color(result.strength_level)

                strength_label.update(
                    f"{emoji} Strength: "
                    f"{result.strength_level.replace('_', ' ').title()} "
                    f"({result.score}/100)"
                )
                strength_label.styles.color = color
            else:
                self.query_one("#strength-label", Label).update("")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "change-btn":
            current_pwd = self.query_one("#current-pwd", Input).value
            new_pwd = self.query_one("#new-pwd", Input).value
            confirm_pwd = self.query_one("#confirm-pwd", Input).value

            # Validation
            if not all([current_pwd, new_pwd, confirm_pwd]):
                self.app.notify("All fields are required", severity="error")
                return

            if new_pwd != confirm_pwd:
                self.app.notify(
                    "New passwords do not match",
                    severity="error"
                )
                return

            # Change password using enhanced function
            success, message = change_password_with_policy(
                self.user_id,
                current_pwd,
                new_pwd,
                self.password_policy
            )

            if success:
                self.app.notify(message, severity="information")
                self.dismiss(True)
            else:
                self.app.notify(message, severity="error")

        else:
            self.dismiss(False)


class PasswordResetRequestModal(ModalScreen[bool]):
    """
    Admin modal to generate password reset token for a user.

    Allows administrators to create secure password reset tokens
    that can be sent to users who forgot their password.
    """

    DEFAULT_CSS = """
    PasswordResetRequestModal {
        align: center middle;
        background: $surface-darken-1;
    }

    PasswordResetRequestModal > Vertical {
        width: 70;
        height: auto;
        border: thick $primary;
        background: $panel;
        padding: 2 4;
    }

    PasswordResetRequestModal Label {
        margin: 1 0;
    }

    PasswordResetRequestModal #title {
        text-align: center;
        text-style: bold;
        color: $accent;
    }

    PasswordResetRequestModal #token-display {
        background: $surface;
        padding: 1 2;
        border: round $primary;
        text-style: bold;
        text-align: center;
        margin: 1 0;
    }

    PasswordResetRequestModal Input {
        margin: 1 0;
    }

    PasswordResetRequestModal Horizontal {
        width: 100%;
        height: auto;
        align-horizontal: center;
        padding-top: 1;
    }

    PasswordResetRequestModal Button {
        margin: 0 1;
    }
    """

    def __init__(self, admin_user_id: int):
        super().__init__()
        self.admin_user_id = admin_user_id
        self.generated_token = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("🔑 Generate Password Reset Token", id="title")
            yield Label(
                "Enter the username of the user who needs a password reset:"
            )
            yield Input(
                placeholder="Username",
                id="username-input"
            )
            yield Label("", id="token-display")
            with Horizontal():
                yield Button(
                    "Generate Token",
                    variant="primary",
                    id="generate-btn"
                )
                yield Button("Close", id="close-btn")

    def on_mount(self) -> None:
        """Focus username input."""
        self.query_one("#username-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "generate-btn":
            username = self.query_one("#username-input", Input).value

            if not username:
                self.app.notify("Username is required", severity="error")
                return

            try:
                # Get user ID
                with get_db_connection() as conn:
                    result = conn.execute(
                        "SELECT id FROM users WHERE username = ?",
                        (username,)
                    ).fetchone()

                    if not result:
                        self.app.notify(
                            f"User '{username}' not found",
                            severity="error"
                        )
                        return

                    user_id = result[0]

                # Generate reset token
                reset_mgr = get_password_reset_manager()
                token, expires_at = reset_mgr.generate_reset_token(
                    user_id,
                    created_by=self.admin_user_id
                )

                self.generated_token = token

                # Display token
                token_label = self.query_one("#token-display", Label)
                token_label.update(
                    f"Token: {token}\n\n"
                    f"Expires: {expires_at}\n\n"
                    "Provide this token to the user to reset their password."
                )

                self.app.notify(
                    "Reset token generated successfully",
                    severity="information"
                )

            except Exception as e:
                self.app.notify(f"Error: {str(e)}", severity="error")

        else:
            self.dismiss(self.generated_token is not None)


class AccountSecurityModal(ModalScreen[None]):
    """
    Display user account security status and quotas.

    Shows security information including lockout status, password age,
    failed login attempts, and resource quotas.
    """

    DEFAULT_CSS = """
    AccountSecurityModal {
        align: center middle;
        background: $surface-darken-1;
    }

    AccountSecurityModal > ScrollableContainer {
        width: 80;
        height: 30;
        border: thick $primary;
        background: $panel;
        padding: 2 4;
    }

    AccountSecurityModal Label {
        margin: 1 0;
    }

    AccountSecurityModal #title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 2;
    }

    AccountSecurityModal #section-title {
        text-style: bold;
        color: $primary;
        margin-top: 2;
    }

    AccountSecurityModal Horizontal {
        width: 100%;
        height: auto;
        align-horizontal: center;
        padding-top: 2;
    }

    AccountSecurityModal Button {
        margin: 0 1;
    }
    """

    def __init__(self, user_id: int, username: str):
        super().__init__()
        self.user_id = user_id
        self.username = username

    def compose(self) -> ComposeResult:
        with ScrollableContainer():
            yield Label(f"🛡️ Account Security: {self.username}", id="title")

            # Load security info
            security_info = self._load_security_info()

            # Account Status Section
            yield Label("Account Status", id="section-title")
            yield Label(f"  Active: {security_info['is_active']}")
            yield Label(f"  Locked: {security_info['account_locked']}")

            if security_info['locked_until']:
                yield Label(f"  Locked Until: {security_info['locked_until']}")

            # Login Security Section
            yield Label("Login Security", id="section-title")
            yield Label(
                f"  Failed Login Attempts: "
                f"{security_info['failed_login_attempts']}"
            )

            if security_info['last_failed_login']:
                yield Label(
                    f"  Last Failed Login: "
                    f"{security_info['last_failed_login']}"
                )

            yield Label(f"  Last Login: {security_info['last_login'] or 'Never'}")

            # Password Section
            yield Label("Password", id="section-title")

            if security_info['password_changed_at']:
                yield Label(
                    f"  Last Changed: {security_info['password_changed_at']}"
                )

            yield Label(
                f"  Force Change Required: "
                f"{security_info['force_password_change']}"
            )

            # Quotas Section
            yield Label("Resource Quotas", id="section-title")

            for quota_name, quota_info in security_info['quotas'].items():
                if quota_info['limit'] == -1:
                    yield Label(f"  {quota_name}: Unlimited")
                else:
                    yield Label(
                        f"  {quota_name}: "
                        f"{quota_info['usage']}/{quota_info['limit']} "
                        f"({quota_info['percentage']:.1f}%)"
                    )

            with Horizontal():
                yield Button("Close", id="close-btn")

    def _load_security_info(self) -> Dict[str, Any]:
        """Load security information from database."""
        with get_db_connection() as conn:
            conn.row_factory = lambda cursor, row: dict(
                zip([col[0] for col in cursor.description], row)
            )

            # Get user info
            user = conn.execute("""
                SELECT
                    is_active,
                    account_locked,
                    locked_until,
                    failed_login_attempts,
                    last_failed_login,
                    password_changed_at,
                    force_password_change,
                    last_login
                FROM users
                WHERE id = ?
            """, (self.user_id,)).fetchone()

        # Get quotas
        quota_mgr = get_quota_manager()
        quotas = quota_mgr.get_all_quotas(self.user_id)

        quota_info = {}
        for quota_type, status in quotas.items():
            quota_info[quota_type.title()] = {
                'usage': status.current_usage,
                'limit': status.quota_limit,
                'percentage': status.percentage_used
            }

        return {
            'is_active': 'Yes' if user['is_active'] else 'No',
            'account_locked': 'Yes' if user['account_locked'] else 'No',
            'locked_until': user['locked_until'],
            'failed_login_attempts': user['failed_login_attempts'] or 0,
            'last_failed_login': user['last_failed_login'],
            'password_changed_at': user['password_changed_at'],
            'force_password_change': 'Yes' if user['force_password_change'] else 'No',
            'last_login': user['last_login'],
            'quotas': quota_info
        }

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        self.dismiss()


class AuditLogViewerModal(ModalScreen[None]):
    """
    Admin modal to view audit log entries.

    Displays recent security events with filtering options.
    """

    DEFAULT_CSS = """
    AuditLogViewerModal {
        align: center middle;
        background: $surface-darken-1;
    }

    AuditLogViewerModal > Vertical {
        width: 90;
        height: 35;
        border: thick $primary;
        background: $panel;
        padding: 2 4;
    }

    AuditLogViewerModal Label {
        margin: 1 0;
    }

    AuditLogViewerModal #title {
        text-align: center;
        text-style: bold;
        color: $accent;
    }

    AuditLogViewerModal DataTable {
        height: 1fr;
        margin: 1 0;
    }

    AuditLogViewerModal #filter-bar {
        height: auto;
        width: 100%;
        margin: 1 0;
    }

    AuditLogViewerModal Input {
        width: 1fr;
        margin: 0 1;
    }

    AuditLogViewerModal Horizontal {
        width: 100%;
        height: auto;
        align-horizontal: center;
        padding-top: 1;
    }

    AuditLogViewerModal Button {
        margin: 0 1;
    }
    """

    def __init__(self, admin_user_id: int):
        super().__init__()
        self.admin_user_id = admin_user_id

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("📋 Audit Log Viewer", id="title")

            # Filter bar
            with Horizontal(id="filter-bar"):
                yield Input(
                    placeholder="Username filter",
                    id="username-filter"
                )
                yield Input(
                    placeholder="Event type filter",
                    id="event-filter"
                )
                yield Button("Refresh", variant="primary", id="refresh-btn")

            # Data table
            table = DataTable(id="audit-table")
            table.cursor_type = "row"
            yield table

            with Horizontal():
                yield Button("Export", id="export-btn")
                yield Button("Close", id="close-btn")

    def on_mount(self) -> None:
        """Initialize table and load data."""
        table = self.query_one(DataTable)

        # Add columns
        table.add_column("ID", width=8)
        table.add_column("Event Type", width=20)
        table.add_column("Username", width=15)
        table.add_column("IP Address", width=15)
        table.add_column("Time", width=20)

        # Load initial data
        self._load_audit_data()

    def _load_audit_data(self) -> None:
        """Load audit log data into table."""
        table = self.query_one(DataTable)
        table.clear()

        # Get filters
        username_filter = self.query_one("#username-filter", Input).value
        event_filter = self.query_one("#event-filter", Input).value

        # Get audit logs
        logger = get_audit_logger()

        filters = {}
        if username_filter:
            # Get user_id from username
            with get_db_connection() as conn:
                result = conn.execute(
                    "SELECT id FROM users WHERE username LIKE ?",
                    (f"%{username_filter}%",)
                ).fetchone()
                if result:
                    filters['user_id'] = result[0]

        if event_filter:
            try:
                filters['event_type'] = AuditEventType(event_filter.lower())
            except ValueError:
                pass

        events = logger.get_events(limit=100, **filters)

        # Add rows
        for event in events:
            table.add_row(
                str(event['id']),
                event['event_type'],
                event['username'] or 'N/A',
                event['ip_address'] or 'N/A',
                event['created_at'][:19]  # Trim to datetime
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "refresh-btn":
            self._load_audit_data()
            self.app.notify("Audit log refreshed", severity="information")

        elif event.button.id == "export-btn":
            # TODO: Implement export functionality
            self.app.notify(
                "Export functionality coming soon",
                severity="information"
            )

        else:
            self.dismiss()


class QuotaManagementModal(ModalScreen[bool]):
    """
    Admin modal to manage user quotas.

    Allows administrators to view and modify user resource quotas.
    """

    DEFAULT_CSS = """
    QuotaManagementModal {
        align: center middle;
        background: $surface-darken-1;
    }

    QuotaManagementModal > Vertical {
        width: 70;
        height: auto;
        border: thick $primary;
        background: $panel;
        padding: 2 4;
    }

    QuotaManagementModal Label {
        margin: 1 0;
    }

    QuotaManagementModal #title {
        text-align: center;
        text-style: bold;
        color: $accent;
    }

    QuotaManagementModal Input {
        margin: 1 0;
    }

    QuotaManagementModal Horizontal {
        width: 100%;
        height: auto;
        align-horizontal: center;
        padding-top: 1;
    }

    QuotaManagementModal Button {
        margin: 0 1;
    }
    """

    def __init__(self, admin_user_id: int, target_user_id: Optional[int] = None):
        super().__init__()
        self.admin_user_id = admin_user_id
        self.target_user_id = target_user_id

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("📊 Manage User Quotas", id="title")

            if self.target_user_id is None:
                yield Label("Enter username:")
                yield Input(placeholder="Username", id="username-input")

            yield Label("Article Quota (-1 for unlimited):")
            yield Input(placeholder="10000", id="article-quota")

            yield Label("Scraper Profile Quota (-1 for unlimited):")
            yield Input(placeholder="100", id="scraper-quota")

            with Horizontal():
                yield Button("Update Quotas", variant="primary", id="update-btn")
                yield Button("Cancel", id="cancel-btn")

    def on_mount(self) -> None:
        """Focus first input."""
        if self.target_user_id is None:
            self.query_one("#username-input", Input).focus()
        else:
            # Load current quotas
            self._load_current_quotas()
            self.query_one("#article-quota", Input).focus()

    def _load_current_quotas(self) -> None:
        """Load current quota values."""
        if self.target_user_id:
            quota_mgr = get_quota_manager()
            quotas = quota_mgr.get_all_quotas(self.target_user_id)

            self.query_one("#article-quota", Input).value = str(
                quotas['articles'].quota_limit
            )
            self.query_one("#scraper-quota", Input).value = str(
                quotas['scrapers'].quota_limit
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "update-btn":
            try:
                # Get target user ID if not already set
                if self.target_user_id is None:
                    username = self.query_one("#username-input", Input).value

                    if not username:
                        self.app.notify("Username is required", severity="error")
                        return

                    with get_db_connection() as conn:
                        result = conn.execute(
                            "SELECT id FROM users WHERE username = ?",
                            (username,)
                        ).fetchone()

                        if not result:
                            self.app.notify(
                                f"User '{username}' not found",
                                severity="error"
                            )
                            return

                        self.target_user_id = result[0]

                # Get quota values
                article_quota_str = self.query_one("#article-quota", Input).value
                scraper_quota_str = self.query_one("#scraper-quota", Input).value

                if not article_quota_str or not scraper_quota_str:
                    self.app.notify("Both quotas are required", severity="error")
                    return

                article_quota = int(article_quota_str)
                scraper_quota = int(scraper_quota_str)

                # Update quotas
                quota_mgr = get_quota_manager()
                quota_mgr.set_user_quota(
                    self.target_user_id,
                    article_quota=article_quota,
                    scraper_quota=scraper_quota,
                    set_by=self.admin_user_id
                )

                self.app.notify("Quotas updated successfully", severity="information")
                self.dismiss(True)

            except ValueError:
                self.app.notify("Quotas must be valid numbers", severity="error")
            except Exception as e:
                self.app.notify(f"Error: {str(e)}", severity="error")

        else:
            self.dismiss(False)
