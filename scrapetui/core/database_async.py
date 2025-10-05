"""
Async database layer using aiosqlite.

Provides async versions of all database operations for improved
performance and scalability in async contexts (FastAPI, async CLI).
"""

import aiosqlite
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class AsyncDatabaseManager:
    """Async database operations manager."""

    def __init__(self, db_path: str | Path):
        """Initialize async database manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._connection: Optional[aiosqlite.Connection] = None

    async def connect(self) -> aiosqlite.Connection:
        """Establish async database connection.

        Returns:
            Active aiosqlite connection
        """
        if self._connection is None:
            self._connection = await aiosqlite.connect(
                self.db_path,
                isolation_level=None  # Autocommit mode
            )
            self._connection.row_factory = aiosqlite.Row
            # Enable foreign keys
            await self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection

    async def close(self):
        """Close async database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def __aenter__(self):
        """Context manager entry."""
        return await self.connect()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()

    # Article Operations

    async def fetch_articles(
        self,
        search: Optional[str] = None,
        tag: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        user_id: Optional[int] = None,
        sentiment: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Fetch articles with optional filters (async).

        Args:
            search: Search term for title/content
            tag: Filter by tag name
            date_from: Filter by start date (ISO format)
            date_to: Filter by end date (ISO format)
            user_id: Filter by owner user ID
            sentiment: Filter by sentiment value
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of article dictionaries
        """
        query = "SELECT * FROM scraped_data WHERE 1=1"
        params = []

        if search:
            query += " AND (title LIKE ? OR content LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%'])

        if tag:
            query += """ AND id IN (
                SELECT article_id FROM article_tags
                JOIN tags ON article_tags.tag_id = tags.id
                WHERE tags.name = ?
            )"""
            params.append(tag)

        if date_from:
            query += " AND timestamp >= ?"
            params.append(date_from)

        if date_to:
            query += " AND timestamp <= ?"
            params.append(date_to)

        if user_id is not None:
            query += " AND user_id = ?"
            params.append(user_id)

        if sentiment:
            query += " AND sentiment = ?"
            params.append(sentiment)

        query += " ORDER BY timestamp DESC"

        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        conn = await self.connect()
        async with conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_article_by_id(self, article_id: int) -> Optional[Dict[str, Any]]:
        """Get single article by ID (async).

        Args:
            article_id: Article ID

        Returns:
            Article dictionary or None if not found
        """
        conn = await self.connect()
        async with conn.execute(
            "SELECT * FROM scraped_data WHERE id = ?",
            (article_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def create_article(self, article_data: Dict[str, Any]) -> int:
        """Create new article (async).

        Args:
            article_data: Article fields dictionary

        Returns:
            ID of created article
        """
        conn = await self.connect()
        cursor = await conn.execute("""
            INSERT INTO scraped_data (
                title, link, content, timestamp, user_id,
                summary, sentiment, keywords, topics
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            article_data.get('title'),
            article_data.get('link'),
            article_data.get('content'),
            article_data.get('timestamp', datetime.now(timezone.utc).isoformat()),
            article_data.get('user_id', 1),
            article_data.get('summary'),
            article_data.get('sentiment'),
            article_data.get('keywords'),
            article_data.get('topics')
        ))
        await conn.commit()
        return cursor.lastrowid

    async def update_article(self, article_id: int, updates: Dict[str, Any]) -> bool:
        """Update article (async).

        Args:
            article_id: Article ID
            updates: Dictionary of fields to update

        Returns:
            True if update successful
        """
        set_clauses = []
        params = []

        for key, value in updates.items():
            set_clauses.append(f"{key} = ?")
            params.append(value)

        params.append(article_id)

        query = f"UPDATE scraped_data SET {', '.join(set_clauses)} WHERE id = ?"

        conn = await self.connect()
        await conn.execute(query, params)
        await conn.commit()
        return True

    async def delete_article(self, article_id: int) -> bool:
        """Delete article (async).

        Args:
            article_id: Article ID

        Returns:
            True if deletion successful
        """
        conn = await self.connect()
        await conn.execute("DELETE FROM scraped_data WHERE id = ?", (article_id,))
        await conn.commit()
        return True

    # User Operations

    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID (async).

        Args:
            user_id: User ID

        Returns:
            User dictionary or None if not found
        """
        conn = await self.connect()
        async with conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username (async).

        Args:
            username: Username to search for

        Returns:
            User dictionary or None if not found
        """
        conn = await self.connect()
        async with conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def create_user(self, user_data: Dict[str, Any]) -> int:
        """Create new user (async).

        Args:
            user_data: User fields dictionary (must include username, password_hash)

        Returns:
            ID of created user
        """
        conn = await self.connect()
        cursor = await conn.execute("""
            INSERT INTO users (
                username, password_hash, email, role, created_at, is_active
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_data['username'],
            user_data['password_hash'],
            user_data.get('email'),
            user_data.get('role', 'user'),
            datetime.now(timezone.utc).isoformat(),
            user_data.get('is_active', 1)
        ))
        await conn.commit()
        return cursor.lastrowid

    async def update_user(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """Update user (async).

        Args:
            user_id: User ID
            updates: Dictionary of fields to update

        Returns:
            True if update successful
        """
        set_clauses = []
        params = []

        for key, value in updates.items():
            set_clauses.append(f"{key} = ?")
            params.append(value)

        params.append(user_id)

        query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?"

        conn = await self.connect()
        await conn.execute(query, params)
        await conn.commit()
        return True

    async def fetch_users(
        self,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Fetch users with optional filters (async).

        Args:
            role: Filter by role
            is_active: Filter by active status
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of user dictionaries
        """
        query = "SELECT * FROM users WHERE 1=1"
        params = []

        if role:
            query += " AND role = ?"
            params.append(role)

        if is_active is not None:
            query += " AND is_active = ?"
            params.append(1 if is_active else 0)

        query += " ORDER BY created_at DESC"

        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        conn = await self.connect()
        async with conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # Session Operations

    async def create_session(
        self,
        user_id: int,
        session_token: str,
        expires_at: str
    ) -> int:
        """Create session (async).

        Args:
            user_id: User ID
            session_token: Unique session token
            expires_at: Expiration timestamp (ISO format)

        Returns:
            ID of created session
        """
        conn = await self.connect()
        cursor = await conn.execute("""
            INSERT INTO user_sessions (session_token, user_id, created_at, expires_at)
            VALUES (?, ?, ?, ?)
        """, (session_token, user_id, datetime.now(timezone.utc).isoformat(), expires_at))
        await conn.commit()
        return cursor.lastrowid

    async def validate_session(self, session_token: str) -> Optional[int]:
        """Validate session and return user_id (async).

        Args:
            session_token: Session token to validate

        Returns:
            User ID if session valid and not expired, None otherwise
        """
        conn = await self.connect()

        # Check if session exists and not expired
        async with conn.execute("""
            SELECT user_id FROM user_sessions
            WHERE session_token = ? AND expires_at > ?
        """, (session_token, datetime.now(timezone.utc).isoformat())) as cursor:
            row = await cursor.fetchone()

            if row:
                return row[0]

            # Clean up expired sessions
            await conn.execute(
                "DELETE FROM user_sessions WHERE expires_at <= ?",
                (datetime.now(timezone.utc).isoformat(),)
            )
            await conn.commit()
            return None

    async def delete_session(self, session_token: str) -> bool:
        """Delete session (logout) (async).

        Args:
            session_token: Session token to delete

        Returns:
            True if deletion successful
        """
        conn = await self.connect()
        await conn.execute(
            "DELETE FROM user_sessions WHERE session_token = ?",
            (session_token,)
        )
        await conn.commit()
        return True

    async def cleanup_expired_sessions(self) -> int:
        """Clean up all expired sessions (async).

        Returns:
            Number of sessions deleted
        """
        conn = await self.connect()
        cursor = await conn.execute(
            "DELETE FROM user_sessions WHERE expires_at <= ?",
            (datetime.now(timezone.utc).isoformat(),)
        )
        await conn.commit()
        return cursor.rowcount


# Global async database manager instance
_async_db_manager: Optional[AsyncDatabaseManager] = None


def get_async_db_manager(db_path: Optional[str | Path] = None) -> AsyncDatabaseManager:
    """Get or create async database manager singleton.

    Args:
        db_path: Optional database path (uses config default if not provided)

    Returns:
        AsyncDatabaseManager instance
    """
    global _async_db_manager

    if _async_db_manager is None:
        from scrapetui.config import get_config
        config = get_config()
        db_path = db_path or config.database_path
        _async_db_manager = AsyncDatabaseManager(db_path)

    return _async_db_manager


async def reset_async_db_manager():
    """Reset async database manager (for testing)."""
    global _async_db_manager
    if _async_db_manager:
        await _async_db_manager.close()
        _async_db_manager = None
