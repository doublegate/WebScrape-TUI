"""Tag model for WebScrape-TUI."""

from dataclasses import dataclass


@dataclass
class Tag:
    """Tag model for article categorization."""

    id: int
    name: str

    def to_dict(self) -> dict:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            'id': self.id,
            'name': self.name
        }

    @classmethod
    def from_db_row(cls, row) -> 'Tag':
        """
        Create Tag from database row.

        Args:
            row: SQLite row object

        Returns:
            Tag instance
        """
        return cls(
            id=row['id'],
            name=row['name']
        )

    def __repr__(self) -> str:
        """String representation."""
        return f"Tag(id={self.id}, name='{self.name}')"

    def __str__(self) -> str:
        """String representation."""
        return self.name
