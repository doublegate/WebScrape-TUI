"""Tag management API endpoints."""

from typing import List

from fastapi import APIRouter, Depends

from ...core.database import get_db_connection
from ...models.user import User
from ...utils.logging import get_logger
from ..models import TagCreate, TagResponse
from ..dependencies import get_current_user, require_user
from ..exceptions import NotFoundException, BadRequestException, ConflictException

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=List[TagResponse])
async def list_tags(current_user: User = Depends(get_current_user)):
    """
    List all tags with article counts.

    Args:
        current_user: Current authenticated user

    Returns:
        List of tags with article counts
    """
    try:
        with get_db_connection() as conn:
            rows = conn.execute("""
                SELECT
                    t.id,
                    t.name,
                    COUNT(at.article_id) as article_count
                FROM tags t
                LEFT JOIN article_tags at ON t.id = at.tag_id
                GROUP BY t.id, t.name
                ORDER BY t.name
            """).fetchall()

            tags = []
            for row in rows:
                tags.append(TagResponse(
                    id=row['id'],
                    name=row['name'],
                    article_count=row['article_count']
                ))

            return tags

    except Exception as e:
        logger.error(f"Error listing tags: {e}")
        raise BadRequestException(detail="Failed to list tags")


@router.post("", response_model=TagResponse, status_code=201)
async def create_tag(
    tag: TagCreate,
    current_user: User = Depends(require_user)
):
    """
    Create new tag.

    Args:
        tag: Tag data
        current_user: Current authenticated user

    Returns:
        Created tag

    Raises:
        ConflictException: If tag already exists
    """
    try:
        with get_db_connection() as conn:
            # Check if tag exists
            existing = conn.execute(
                "SELECT id FROM tags WHERE name = ?",
                (tag.name,)
            ).fetchone()

            if existing:
                raise ConflictException(detail="Tag already exists")

            # Insert tag
            cursor = conn.execute(
                "INSERT INTO tags (name) VALUES (?)",
                (tag.name,)
            )

            tag_id = cursor.lastrowid
            conn.commit()

            logger.info(f"Tag {tag_id} created by user {current_user.id}")

            return TagResponse(
                id=tag_id,
                name=tag.name,
                article_count=0
            )

    except ConflictException:
        raise
    except Exception as e:
        logger.error(f"Error creating tag: {e}")
        raise BadRequestException(detail="Failed to create tag")


@router.delete("/{tag_id}", status_code=204)
async def delete_tag(
    tag_id: int,
    current_user: User = Depends(require_user)
):
    """
    Delete tag.

    Args:
        tag_id: Tag ID
        current_user: Current authenticated user

    Raises:
        NotFoundException: If tag not found
    """
    try:
        with get_db_connection() as conn:
            # Check tag exists
            row = conn.execute(
                "SELECT id FROM tags WHERE id = ?",
                (tag_id,)
            ).fetchone()

            if not row:
                raise NotFoundException(detail="Tag not found")

            # Delete tag (cascade will delete associations)
            conn.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
            conn.commit()

            logger.info(f"Tag {tag_id} deleted by user {current_user.id}")

    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tag {tag_id}: {e}")
        raise BadRequestException(detail="Failed to delete tag")


@router.get("/{tag_id}/articles", response_model=List[int])
async def get_articles_by_tag(
    tag_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Get article IDs associated with tag.

    Args:
        tag_id: Tag ID
        current_user: Current authenticated user

    Returns:
        List of article IDs

    Raises:
        NotFoundException: If tag not found
    """
    try:
        with get_db_connection() as conn:
            # Check tag exists
            tag_row = conn.execute(
                "SELECT id FROM tags WHERE id = ?",
                (tag_id,)
            ).fetchone()

            if not tag_row:
                raise NotFoundException(detail="Tag not found")

            # Get article IDs
            rows = conn.execute("""
                SELECT at.article_id
                FROM article_tags at
                JOIN scraped_data sd ON at.article_id = sd.id
                WHERE at.tag_id = ?
                ORDER BY sd.timestamp DESC
            """, (tag_id,)).fetchall()

            article_ids = [row['article_id'] for row in rows]
            return article_ids

    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"Error getting articles for tag {tag_id}: {e}")
        raise BadRequestException(detail="Failed to get articles for tag")
