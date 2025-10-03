"""Article model for WebScrape-TUI."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Article:
    """Article model representing scraped content."""

    id: int
    url: str
    title: Optional[str]
    content: Optional[str]
    summary: Optional[str]
    link: str
    timestamp: str
    sentiment: Optional[str]
    user_id: int

    @property
    def timestamp_datetime(self) -> datetime:
        """
        Get timestamp as datetime object.

        Returns:
            Timestamp datetime
        """
        return datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))

    @property
    def has_summary(self) -> bool:
        """
        Check if article has summary.

        Returns:
            True if summary exists
        """
        return bool(self.summary)

    @property
    def has_sentiment(self) -> bool:
        """
        Check if article has sentiment analysis.

        Returns:
            True if sentiment exists
        """
        return bool(self.sentiment)

    @property
    def content_length(self) -> int:
        """
        Get content length in characters.

        Returns:
            Content length
        """
        return len(self.content) if self.content else 0

    @property
    def summary_length(self) -> int:
        """
        Get summary length in characters.

        Returns:
            Summary length
        """
        return len(self.summary) if self.summary else 0

    def to_dict(self, include_content: bool = False) -> dict:
        """
        Convert to dictionary.

        Args:
            include_content: Whether to include full content and summary

        Returns:
            Dictionary representation
        """
        data = {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'link': self.link,
            'timestamp': self.timestamp,
            'sentiment': self.sentiment,
            'user_id': self.user_id,
            'has_summary': self.has_summary,
            'has_sentiment': self.has_sentiment,
            'content_length': self.content_length,
            'summary_length': self.summary_length
        }

        if include_content:
            data['content'] = self.content
            data['summary'] = self.summary

        return data

    @classmethod
    def from_db_row(cls, row) -> 'Article':
        """
        Create Article from database row.

        Args:
            row: SQLite row object

        Returns:
            Article instance
        """
        return cls(
            id=row['id'],
            url=row['url'],
            title=row.get('title'),
            content=row.get('content'),
            summary=row.get('summary'),
            link=row['link'],
            timestamp=row['timestamp'],
            sentiment=row.get('sentiment'),
            user_id=row.get('user_id', 1)
        )

    def __repr__(self) -> str:
        """String representation."""
        return f"Article(id={self.id}, title='{self.title[:30] if self.title else 'None'}...', user_id={self.user_id})"
