"""Scraper profile model for WebScrape-TUI."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ScraperProfile:
    """Scraper profile model representing a scraper configuration."""

    id: int
    name: str
    url: str
    selector: str
    default_limit: int
    default_tags_csv: Optional[str]
    description: Optional[str]
    is_preinstalled: bool
    user_id: int
    is_shared: bool

    @property
    def is_editable(self) -> bool:
        """
        Check if scraper can be edited (not preinstalled).

        Returns:
            True if scraper can be edited
        """
        return not self.is_preinstalled

    @property
    def visibility(self) -> str:
        """
        Get visibility status.

        Returns:
            'shared' or 'private'
        """
        if self.is_shared:
            return "shared"
        return "private"

    @property
    def tags_list(self) -> list:
        """
        Get default tags as list.

        Returns:
            List of tag strings
        """
        if self.default_tags_csv:
            return [tag.strip() for tag in self.default_tags_csv.split(',') if tag.strip()]
        return []

    def to_dict(self) -> dict:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'selector': self.selector,
            'default_limit': self.default_limit,
            'default_tags_csv': self.default_tags_csv,
            'description': self.description,
            'is_preinstalled': self.is_preinstalled,
            'user_id': self.user_id,
            'is_shared': self.is_shared,
            'visibility': self.visibility,
            'is_editable': self.is_editable,
            'tags_list': self.tags_list
        }

    @classmethod
    def from_db_row(cls, row) -> 'ScraperProfile':
        """
        Create ScraperProfile from database row.

        Args:
            row: SQLite row object

        Returns:
            ScraperProfile instance
        """
        return cls(
            id=row['id'],
            name=row['name'],
            url=row['url'],
            selector=row['selector'],
            default_limit=row.get('default_limit', 0),
            default_tags_csv=row.get('default_tags_csv'),
            description=row.get('description'),
            is_preinstalled=bool(row.get('is_preinstalled', 0)),
            user_id=row.get('user_id', 1),
            is_shared=bool(row.get('is_shared', 0))
        )

    def __repr__(self) -> str:
        """String representation."""
        return f"ScraperProfile(id={self.id}, name='{self.name}', visibility='{self.visibility}')"
