"""Scraper management and scraping API endpoints."""

from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends

from ...core.database import get_db_connection
from ...core.permissions import can_edit, can_delete
from ...models.user import User
from ...scrapers.manager import get_scraper_manager
from ...utils.logging import get_logger
from ..models import (
    ScraperProfileCreate,
    ScraperProfileUpdate,
    ScraperProfileResponse,
    ScrapeRequest,
    ScrapeResult,
    ArticleResponse
)
from ..dependencies import get_current_user, require_user
from ..exceptions import NotFoundException, ForbiddenException, BadRequestException

logger = get_logger(__name__)
router = APIRouter()
scraper_manager = get_scraper_manager()


@router.get("/available", response_model=List[dict])
async def list_available_scrapers(current_user: User = Depends(get_current_user)):
    """
    List all available scrapers (built-in and plugins).

    Args:
        current_user: Current authenticated user

    Returns:
        List of scraper metadata
    """
    try:
        scrapers = scraper_manager.list_scrapers()
        return scrapers
    except Exception as e:
        logger.error(f"Error listing scrapers: {e}")
        raise BadRequestException(detail="Failed to list scrapers")


@router.get("/profiles", response_model=List[ScraperProfileResponse])
async def list_scraper_profiles(current_user: User = Depends(get_current_user)):
    """
    List saved scraper profiles.

    Args:
        current_user: Current authenticated user

    Returns:
        List of scraper profiles (user's own + shared + preinstalled)
    """
    try:
        with get_db_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM saved_scrapers
                WHERE user_id = ? OR is_shared = 1 OR is_preinstalled = 1
                ORDER BY name
            """, (current_user.id,)).fetchall()

            profiles = []
            for row in rows:
                profiles.append(ScraperProfileResponse(
                    id=row['id'],
                    name=row['name'],
                    url=row['url'],
                    selector=row['selector'],
                    default_limit=row['default_limit'] or 0,
                    default_tags_csv=row['default_tags_csv'],
                    description=row['description'],
                    is_preinstalled=bool(row['is_preinstalled']),
                    user_id=row['user_id'],
                    is_shared=bool(row['is_shared'])
                ))

            return profiles

    except Exception as e:
        logger.error(f"Error listing scraper profiles: {e}")
        raise BadRequestException(detail="Failed to list scraper profiles")


@router.post("/profiles", response_model=ScraperProfileResponse, status_code=201)
async def create_scraper_profile(
    profile: ScraperProfileCreate,
    current_user: User = Depends(require_user)
):
    """
    Create new scraper profile.

    Args:
        profile: Scraper profile data
        current_user: Current authenticated user

    Returns:
        Created scraper profile
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO saved_scrapers
                (name, url, selector, default_limit, default_tags_csv,
                 description, user_id, is_shared)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile.name,
                profile.url,
                profile.selector,
                profile.default_limit,
                profile.default_tags_csv,
                profile.description,
                current_user.id,
                1 if profile.is_shared else 0
            ))

            profile_id = cursor.lastrowid
            conn.commit()

            logger.info(f"Scraper profile {profile_id} created by user {current_user.id}")

            return ScraperProfileResponse(
                id=profile_id,
                name=profile.name,
                url=profile.url,
                selector=profile.selector,
                default_limit=profile.default_limit,
                default_tags_csv=profile.default_tags_csv,
                description=profile.description,
                is_preinstalled=False,
                user_id=current_user.id,
                is_shared=profile.is_shared
            )

    except Exception as e:
        logger.error(f"Error creating scraper profile: {e}")
        raise BadRequestException(detail="Failed to create scraper profile")


@router.put("/profiles/{profile_id}", response_model=ScraperProfileResponse)
async def update_scraper_profile(
    profile_id: int,
    profile_update: ScraperProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update scraper profile.

    Args:
        profile_id: Profile ID
        profile_update: Updated profile data
        current_user: Current authenticated user

    Returns:
        Updated scraper profile

    Raises:
        NotFoundException: If profile not found
        ForbiddenException: If user doesn't have permission
    """
    try:
        with get_db_connection() as conn:
            # Check profile exists and get owner
            row = conn.execute(
                "SELECT user_id, is_preinstalled FROM saved_scrapers WHERE id = ?",
                (profile_id,)
            ).fetchone()

            if not row:
                raise NotFoundException(detail="Scraper profile not found")

            # Cannot edit preinstalled scrapers
            if row['is_preinstalled']:
                raise ForbiddenException(detail="Cannot edit preinstalled scraper profiles")

            # Check permissions
            if not can_edit(current_user.id, row['user_id']):
                raise ForbiddenException(detail="Cannot edit this scraper profile")

            # Build update query
            updates = []
            params = []

            if profile_update.url is not None:
                updates.append("url = ?")
                params.append(profile_update.url)

            if profile_update.selector is not None:
                updates.append("selector = ?")
                params.append(profile_update.selector)

            if profile_update.default_limit is not None:
                updates.append("default_limit = ?")
                params.append(profile_update.default_limit)

            if profile_update.default_tags_csv is not None:
                updates.append("default_tags_csv = ?")
                params.append(profile_update.default_tags_csv)

            if profile_update.description is not None:
                updates.append("description = ?")
                params.append(profile_update.description)

            if profile_update.is_shared is not None:
                updates.append("is_shared = ?")
                params.append(1 if profile_update.is_shared else 0)

            if updates:
                sql = f"UPDATE saved_scrapers SET {', '.join(updates)} WHERE id = ?"
                params.append(profile_id)
                conn.execute(sql, params)
                conn.commit()

            # Fetch updated profile
            row = conn.execute(
                "SELECT * FROM saved_scrapers WHERE id = ?",
                (profile_id,)
            ).fetchone()

            logger.info(f"Scraper profile {profile_id} updated by user {current_user.id}")

            return ScraperProfileResponse(
                id=row['id'],
                name=row['name'],
                url=row['url'],
                selector=row['selector'],
                default_limit=row['default_limit'] or 0,
                default_tags_csv=row['default_tags_csv'],
                description=row['description'],
                is_preinstalled=bool(row['is_preinstalled']),
                user_id=row['user_id'],
                is_shared=bool(row['is_shared'])
            )

    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error updating scraper profile {profile_id}: {e}")
        raise BadRequestException(detail="Failed to update scraper profile")


@router.delete("/profiles/{profile_id}", status_code=204)
async def delete_scraper_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Delete scraper profile.

    Args:
        profile_id: Profile ID
        current_user: Current authenticated user

    Raises:
        NotFoundException: If profile not found
        ForbiddenException: If user doesn't have permission
    """
    try:
        with get_db_connection() as conn:
            # Check profile exists and get owner
            row = conn.execute(
                "SELECT user_id, is_preinstalled FROM saved_scrapers WHERE id = ?",
                (profile_id,)
            ).fetchone()

            if not row:
                raise NotFoundException(detail="Scraper profile not found")

            # Cannot delete preinstalled scrapers
            if row['is_preinstalled']:
                raise ForbiddenException(detail="Cannot delete preinstalled scraper profiles")

            # Check permissions
            if not can_delete(current_user.id, row['user_id']):
                raise ForbiddenException(detail="Cannot delete this scraper profile")

            # Delete profile
            conn.execute("DELETE FROM saved_scrapers WHERE id = ?", (profile_id,))
            conn.commit()

            logger.info(f"Scraper profile {profile_id} deleted by user {current_user.id}")

    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error deleting scraper profile {profile_id}: {e}")
        raise BadRequestException(detail="Failed to delete scraper profile")


@router.post("/scrape", response_model=ScrapeResult, status_code=201)
async def scrape_url(
    request: ScrapeRequest,
    current_user: User = Depends(require_user)
):
    """
    Scrape URL and save article.

    Args:
        request: Scraping request with URL and options
        current_user: Current authenticated user

    Returns:
        Scraping result with article data
    """
    try:
        # Scrape URL using scraper manager
        result = scraper_manager.scrape_url(
            request.url,
            scraper_name=request.scraper_name
        )

        if not result.success:
            return ScrapeResult(
                success=False,
                article=None,
                error=result.error or "Scraping failed"
            )

        # Save article to database
        with get_db_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO scraped_data
                (url, title, content, link, user_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                result.url,
                result.title,
                result.content,
                result.link,
                current_user.id,
                datetime.now().isoformat()
            ))

            article_id = cursor.lastrowid

            # Add tags if provided
            if request.tags:
                for tag_name in request.tags:
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

            # Fetch created article
            row = conn.execute(
                "SELECT * FROM scraped_data WHERE id = ?",
                (article_id,)
            ).fetchone()

            # Get tags
            tag_rows = conn.execute("""
                SELECT t.name FROM tags t
                JOIN article_tags at ON t.id = at.tag_id
                WHERE at.article_id = ?
            """, (article_id,)).fetchall()
            tags = [t['name'] for t in tag_rows]

        logger.info(f"URL scraped and article {article_id} created by user {current_user.id}")

        article_response = ArticleResponse(
            id=article_id,
            url=row['url'],
            title=row['title'],
            content=row['content'],
            link=row['link'],
            summary=row['summary'],
            sentiment=row['sentiment'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            user_id=row['user_id'],
            tags=tags
        )

        return ScrapeResult(
            success=True,
            article=article_response,
            error=None
        )

    except Exception as e:
        logger.error(f"Error scraping URL {request.url}: {e}")
        return ScrapeResult(
            success=False,
            article=None,
            error=str(e)
        )
