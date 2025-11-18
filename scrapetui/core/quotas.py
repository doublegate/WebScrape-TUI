"""
User Quotas System

Implements resource quotas for users to prevent abuse and manage system resources.
Tracks article and scraper profile limits per user or role.

Part of v2.2.0 Administrative Features.
"""

import sqlite3
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from .audit import log_audit_event, AuditEventType


class QuotaType(Enum):
    """Types of quotas."""
    ARTICLES = "articles"
    SCRAPERS = "scrapers"


@dataclass
class QuotaConfig:
    """Default quota configuration."""
    default_article_quota: int = 10000
    default_scraper_quota: int = 100
    admin_unlimited: bool = True  # Admins bypass quotas


@dataclass
class QuotaStatus:
    """Quota status for a user."""
    quota_type: str
    current_usage: int
    quota_limit: int
    remaining: int
    percentage_used: float
    exceeded: bool


class QuotaManager:
    """Manages user quotas and enforcement."""

    def __init__(
        self,
        db_path: str = "scraped_data_tui_v1.0.db",
        config: QuotaConfig = None
    ):
        """
        Initialize quota manager.

        Args:
            db_path: Path to SQLite database
            config: Quota configuration
        """
        self.db_path = db_path
        self.config = config or QuotaConfig()
        self._ensure_quota_columns()

    def _ensure_quota_columns(self):
        """Ensure quota columns exist in users table."""
        with sqlite3.connect(self.db_path) as conn:
            # Add quota columns
            try:
                conn.execute("""
                    ALTER TABLE users ADD COLUMN article_quota
                    INTEGER NOT NULL DEFAULT ?
                """, (self.config.default_article_quota,))
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                conn.execute("""
                    ALTER TABLE users ADD COLUMN scraper_quota
                    INTEGER NOT NULL DEFAULT ?
                """, (self.config.default_scraper_quota,))
            except sqlite3.OperationalError:
                pass  # Column already exists

            conn.commit()

    def get_quota_status(
        self,
        user_id: int,
        quota_type: QuotaType
    ) -> QuotaStatus:
        """
        Get current quota status for a user.

        Args:
            user_id: User ID
            quota_type: Type of quota to check

        Returns:
            QuotaStatus object with current status

        Example:
            >>> mgr = QuotaManager()
            >>> status = mgr.get_quota_status(1, QuotaType.ARTICLES)
            >>> print(f"Used: {status.current_usage}/{status.quota_limit}")
            >>> print(f"Remaining: {status.remaining}")
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get user quota limit
            user = conn.execute("""
                SELECT article_quota, scraper_quota, role
                FROM users
                WHERE id = ?
            """, (user_id,)).fetchone()

            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            # Admins bypass quotas
            if self.config.admin_unlimited and user['role'] == 'admin':
                return QuotaStatus(
                    quota_type=quota_type.value,
                    current_usage=0,
                    quota_limit=-1,  # -1 indicates unlimited
                    remaining=-1,
                    percentage_used=0.0,
                    exceeded=False
                )

            # Get quota limit
            if quota_type == QuotaType.ARTICLES:
                quota_limit = user['article_quota']
                # Count user's articles
                current_usage = conn.execute("""
                    SELECT COUNT(*) as count
                    FROM scraped_data
                    WHERE user_id = ?
                """, (user_id,)).fetchone()['count']
            else:  # SCRAPERS
                quota_limit = user['scraper_quota']
                # Count user's scraper profiles
                current_usage = conn.execute("""
                    SELECT COUNT(*) as count
                    FROM saved_scrapers
                    WHERE user_id = ?
                """, (user_id,)).fetchone()['count']

            remaining = max(0, quota_limit - current_usage)
            percentage_used = (current_usage / quota_limit * 100) if quota_limit > 0 else 0
            exceeded = current_usage >= quota_limit

            return QuotaStatus(
                quota_type=quota_type.value,
                current_usage=current_usage,
                quota_limit=quota_limit,
                remaining=remaining,
                percentage_used=percentage_used,
                exceeded=exceeded
            )

    def check_quota(
        self,
        user_id: int,
        quota_type: QuotaType
    ) -> bool:
        """
        Check if user has quota available.

        Args:
            user_id: User ID
            quota_type: Type of quota to check

        Returns:
            True if quota available, False if exceeded
        """
        status = self.get_quota_status(user_id, quota_type)

        # -1 means unlimited (admin)
        if status.quota_limit == -1:
            return True

        if status.exceeded:
            # Log quota exceeded event
            with sqlite3.connect(self.db_path) as conn:
                user = conn.execute("""
                    SELECT username FROM users WHERE id = ?
                """, (user_id,)).fetchone()

                if user:
                    log_audit_event(
                        AuditEventType.QUOTA_EXCEEDED,
                        user_id=user_id,
                        username=user[0],
                        event_data={
                            'quota_type': quota_type.value,
                            'current_usage': status.current_usage,
                            'quota_limit': status.quota_limit
                        }
                    )

        return not status.exceeded

    def set_user_quota(
        self,
        user_id: int,
        article_quota: Optional[int] = None,
        scraper_quota: Optional[int] = None,
        set_by: Optional[int] = None
    ) -> None:
        """
        Set quota limits for a user.

        Args:
            user_id: User ID
            article_quota: New article quota (None to keep current)
            scraper_quota: New scraper quota (None to keep current)
            set_by: Admin user ID who set the quota

        Example:
            >>> mgr = QuotaManager()
            >>> mgr.set_user_quota(
            ...     user_id=5,
            ...     article_quota=20000,
            ...     scraper_quota=200,
            ...     set_by=1  # admin user
            ... )
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get current values
            user = conn.execute("""
                SELECT username, article_quota, scraper_quota
                FROM users
                WHERE id = ?
            """, (user_id,)).fetchone()

            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            updates = []
            params = []

            if article_quota is not None:
                updates.append("article_quota = ?")
                params.append(article_quota)

            if scraper_quota is not None:
                updates.append("scraper_quota = ?")
                params.append(scraper_quota)

            if not updates:
                return  # Nothing to update

            params.append(user_id)

            # Update quotas
            query = f"""
                UPDATE users
                SET {', '.join(updates)}
                WHERE id = ?
            """
            conn.execute(query, params)
            conn.commit()

            # Log audit event
            log_audit_event(
                AuditEventType.QUOTA_CHANGED,
                user_id=user_id,
                username=user['username'],
                event_data={
                    'old_article_quota': user['article_quota'],
                    'new_article_quota': article_quota,
                    'old_scraper_quota': user['scraper_quota'],
                    'new_scraper_quota': scraper_quota,
                    'set_by': set_by
                }
            )

    def get_all_quotas(self, user_id: int) -> Dict[str, QuotaStatus]:
        """
        Get all quota statuses for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary of quota type to QuotaStatus
        """
        return {
            'articles': self.get_quota_status(user_id, QuotaType.ARTICLES),
            'scrapers': self.get_quota_status(user_id, QuotaType.SCRAPERS)
        }

    def get_quota_summary(self) -> Dict[str, Any]:
        """
        Get system-wide quota usage summary.

        Returns:
            Dictionary with quota statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get users near quota limits (>80% usage)
            near_limit_articles = conn.execute("""
                SELECT u.id, u.username, COUNT(sd.id) as usage, u.article_quota
                FROM users u
                LEFT JOIN scraped_data sd ON u.id = sd.user_id
                WHERE u.article_quota > 0
                GROUP BY u.id
                HAVING usage >= (u.article_quota * 0.8)
            """).fetchall()

            near_limit_scrapers = conn.execute("""
                SELECT u.id, u.username, COUNT(ss.id) as usage, u.scraper_quota
                FROM users u
                LEFT JOIN saved_scrapers ss ON u.id = ss.user_id
                WHERE u.scraper_quota > 0
                GROUP BY u.id
                HAVING usage >= (u.scraper_quota * 0.8)
            """).fetchall()

            # Get users who exceeded quotas
            exceeded_articles = conn.execute("""
                SELECT u.id, u.username, COUNT(sd.id) as usage, u.article_quota
                FROM users u
                LEFT JOIN scraped_data sd ON u.id = sd.user_id
                WHERE u.article_quota > 0
                GROUP BY u.id
                HAVING usage >= u.article_quota
            """).fetchall()

            exceeded_scrapers = conn.execute("""
                SELECT u.id, u.username, COUNT(ss.id) as usage, u.scraper_quota
                FROM users u
                LEFT JOIN saved_scrapers ss ON u.id = ss.user_id
                WHERE u.scraper_quota > 0
                GROUP BY u.id
                HAVING usage >= u.scraper_quota
            """).fetchall()

            return {
                'articles': {
                    'near_limit': [dict(row) for row in near_limit_articles],
                    'exceeded': [dict(row) for row in exceeded_articles]
                },
                'scrapers': {
                    'near_limit': [dict(row) for row in near_limit_scrapers],
                    'exceeded': [dict(row) for row in exceeded_scrapers]
                }
            }


# Global quota manager instance
_quota_manager: Optional[QuotaManager] = None


def get_quota_manager(
    db_path: str = "scraped_data_tui_v1.0.db",
    config: QuotaConfig = None
) -> QuotaManager:
    """
    Get or create global quota manager instance.

    Args:
        db_path: Path to database
        config: Quota configuration

    Returns:
        QuotaManager instance
    """
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = QuotaManager(db_path, config)
    return _quota_manager
