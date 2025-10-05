"""Article management API endpoints."""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query

from ...core.database import get_db_connection
from ...core.permissions import can_edit, can_delete, is_admin
from ...models.user import User
from ...models.article import Article
from ...utils.logging import get_logger
from ..models import (
    ArticleCreate,
    ArticleUpdate,
    ArticleResponse,
    ArticleListResponse
)
from ..dependencies import get_current_user, require_user
from ..exceptions import NotFoundException, ForbiddenException, BadRequestException

logger = get_logger(__name__)
router = APIRouter()


def article_to_response(article: Article, include_tags: bool = True) -> ArticleResponse:
    """
    Convert Article model to API response.

    Args:
        article: Article model instance
        include_tags: Whether to include tags

    Returns:
        ArticleResponse model
    """
    tags = None
    if include_tags:
        try:
            with get_db_connection() as conn:
                tag_rows = conn.execute("""
                    SELECT t.name FROM tags t
                    JOIN article_tags at ON t.id = at.tag_id
                    WHERE at.article_id = ?
                """, (article.id,)).fetchall()
                tags = [row['name'] for row in tag_rows]
        except Exception as e:
            logger.error(f"Error fetching tags for article {article.id}: {e}")
            tags = []

    return ArticleResponse(
        id=article.id,
        url=article.url,
        title=article.title,
        content=article.content,
        link=article.link,
        summary=article.summary,
        sentiment=article.sentiment,
        timestamp=article.timestamp_datetime,
        user_id=article.user_id,
        tags=tags
    )


@router.get("", response_model=ArticleListResponse)
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    query: Optional[str] = None,
    tags: Optional[str] = None,
    sentiment: Optional[str] = None,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """
    List articles with pagination and filtering.

    Args:
        page: Page number (1-indexed)
        page_size: Number of articles per page
        query: Search query (searches title and content)
        tags: Comma-separated tag filter
        sentiment: Sentiment filter
        user_id: Filter by user ID (admin only)
        current_user: Current authenticated user

    Returns:
        Paginated list of articles
    """
    offset = (page - 1) * page_size

    # Build WHERE clause
    where_clauses = []
    params = []

    # User filtering (non-admin users can only see own articles and shared articles)
    if not is_admin(current_user.id):
        where_clauses.append("(scraped_data.user_id = ? OR saved_scrapers.is_shared = 1)")
        params.append(current_user.id)
    elif user_id is not None:
        where_clauses.append("scraped_data.user_id = ?")
        params.append(user_id)

    # Search query
    if query:
        where_clauses.append("(title LIKE ? OR content LIKE ?)")
        search_term = f"%{query}%"
        params.extend([search_term, search_term])

    # Sentiment filter
    if sentiment:
        where_clauses.append("sentiment = ?")
        params.append(sentiment)

    # Tags filter
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        placeholders = ",".join(["?"] * len(tag_list))
        where_clauses.append(f"""
            scraped_data.id IN (
                SELECT at.article_id FROM article_tags at
                JOIN tags t ON at.tag_id = t.id
                WHERE t.name IN ({placeholders})
            )
        """)
        params.extend(tag_list)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Get total count
    try:
        with get_db_connection() as conn:
            count_sql = f"SELECT COUNT(*) as cnt FROM scraped_data WHERE {where_sql}"
            total = conn.execute(count_sql, params).fetchone()['cnt']

            # Get articles
            sql = f"""
                SELECT * FROM scraped_data
                WHERE {where_sql}
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """
            params.extend([page_size, offset])

            rows = conn.execute(sql, params).fetchall()
            articles = [Article.from_db_row(row) for row in rows]

    except Exception as e:
        logger.error(f"Error listing articles: {e}")
        raise BadRequestException(detail="Failed to fetch articles")

    # Convert to response models
    article_responses = [article_to_response(article) for article in articles]

    pages = (total + page_size - 1) // page_size

    return ArticleListResponse(
        articles=article_responses,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Get single article by ID.

    Args:
        article_id: Article ID
        current_user: Current authenticated user

    Returns:
        Article details

    Raises:
        NotFoundException: If article not found
        ForbiddenException: If user doesn't have access
    """
    try:
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT * FROM scraped_data WHERE id = ?",
                (article_id,)
            ).fetchone()

            if not row:
                raise NotFoundException(detail="Article not found")

            article = Article.from_db_row(row)

            # Check permissions
            if not is_admin(current_user.id) and article.user_id != current_user.id:
                raise ForbiddenException(detail="Access denied")

            return article_to_response(article)

    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error fetching article {article_id}: {e}")
        raise BadRequestException(detail="Failed to fetch article")


@router.post("", response_model=ArticleResponse, status_code=201)
async def create_article(
    article: ArticleCreate,
    current_user: User = Depends(require_user)
):
    """
    Create new article (manual entry).

    Args:
        article: Article data
        current_user: Current authenticated user

    Returns:
        Created article

    Raises:
        BadRequestException: If creation fails
    """
    try:
        with get_db_connection() as conn:
            # Insert article
            cursor = conn.execute("""
                INSERT INTO scraped_data
                (url, title, content, link, summary, sentiment, user_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                article.url,
                article.title,
                article.content,
                article.link,
                article.summary,
                article.sentiment,
                current_user.id,
                datetime.now().isoformat()
            ))

            article_id = cursor.lastrowid

            # Add tags if provided
            if article.tags:
                for tag_name in article.tags:
                    # Get or create tag
                    tag_row = conn.execute(
                        "SELECT id FROM tags WHERE name = ?",
                        (tag_name,)
                    ).fetchone()

                    if tag_row:
                        tag_id = tag_row['id']
                    else:
                        tag_cursor = conn.execute(
                            "INSERT INTO tags (name) VALUES (?)",
                            (tag_name,)
                        )
                        tag_id = tag_cursor.lastrowid

                    # Associate tag with article
                    conn.execute(
                        "INSERT OR IGNORE INTO article_tags (article_id, tag_id) VALUES (?, ?)",
                        (article_id, tag_id)
                    )

            conn.commit()

            # Fetch created article
            row = conn.execute(
                "SELECT * FROM scraped_data WHERE id = ?",
                (article_id,)
            ).fetchone()

            created_article = Article.from_db_row(row)
            logger.info(f"Article {article_id} created by user {current_user.id}")

            return article_to_response(created_article)

    except Exception as e:
        logger.error(f"Error creating article: {e}")
        raise BadRequestException(detail="Failed to create article")


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    article_update: ArticleUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update existing article.

    Args:
        article_id: Article ID
        article_update: Updated article data
        current_user: Current authenticated user

    Returns:
        Updated article

    Raises:
        NotFoundException: If article not found
        ForbiddenException: If user doesn't have permission
    """
    try:
        with get_db_connection() as conn:
            # Check article exists and get owner
            row = conn.execute(
                "SELECT user_id FROM scraped_data WHERE id = ?",
                (article_id,)
            ).fetchone()

            if not row:
                raise NotFoundException(detail="Article not found")

            # Check permissions
            if not can_edit(current_user.id, row['user_id']):
                raise ForbiddenException(detail="Cannot edit this article")

            # Build update query
            updates = []
            params = []

            if article_update.title is not None:
                updates.append("title = ?")
                params.append(article_update.title)

            if article_update.content is not None:
                updates.append("content = ?")
                params.append(article_update.content)

            if article_update.summary is not None:
                updates.append("summary = ?")
                params.append(article_update.summary)

            if article_update.sentiment is not None:
                updates.append("sentiment = ?")
                params.append(article_update.sentiment)

            if updates:
                sql = f"UPDATE scraped_data SET {', '.join(updates)} WHERE id = ?"
                params.append(article_id)
                conn.execute(sql, params)

            # Update tags if provided
            if article_update.tags is not None:
                # Remove existing tags
                conn.execute("DELETE FROM article_tags WHERE article_id = ?", (article_id,))

                # Add new tags
                for tag_name in article_update.tags:
                    # Get or create tag
                    tag_row = conn.execute(
                        "SELECT id FROM tags WHERE name = ?",
                        (tag_name,)
                    ).fetchone()

                    if tag_row:
                        tag_id = tag_row['id']
                    else:
                        tag_cursor = conn.execute(
                            "INSERT INTO tags (name) VALUES (?)",
                            (tag_name,)
                        )
                        tag_id = tag_cursor.lastrowid

                    conn.execute(
                        "INSERT OR IGNORE INTO article_tags (article_id, tag_id) VALUES (?, ?)",
                        (article_id, tag_id)
                    )

            conn.commit()

            # Fetch updated article
            row = conn.execute(
                "SELECT * FROM scraped_data WHERE id = ?",
                (article_id,)
            ).fetchone()

            updated_article = Article.from_db_row(row)
            logger.info(f"Article {article_id} updated by user {current_user.id}")

            return article_to_response(updated_article)

    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error updating article {article_id}: {e}")
        raise BadRequestException(detail="Failed to update article")


@router.delete("/{article_id}", status_code=204)
async def delete_article(
    article_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Delete article.

    Args:
        article_id: Article ID
        current_user: Current authenticated user

    Raises:
        NotFoundException: If article not found
        ForbiddenException: If user doesn't have permission
    """
    try:
        with get_db_connection() as conn:
            # Check article exists and get owner
            row = conn.execute(
                "SELECT user_id FROM scraped_data WHERE id = ?",
                (article_id,)
            ).fetchone()

            if not row:
                raise NotFoundException(detail="Article not found")

            # Check permissions
            if not can_delete(current_user.id, row['user_id']):
                raise ForbiddenException(detail="Cannot delete this article")

            # Delete article (cascade will delete tags association)
            conn.execute("DELETE FROM scraped_data WHERE id = ?", (article_id,))
            conn.commit()

            logger.info(f"Article {article_id} deleted by user {current_user.id}")

    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error deleting article {article_id}: {e}")
        raise BadRequestException(detail="Failed to delete article")
