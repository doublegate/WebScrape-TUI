"""AI-powered analysis API endpoints (summarization, sentiment, entities, Q&A)."""

from typing import List, Dict, Any

from fastapi import APIRouter, Depends

from ...core.database import get_db_connection
from ...models.user import User
from ...models.article import Article
from ...utils.logging import get_logger
from ..models import (
    SummarizeRequest,
    SummarizeResponse,
    SentimentRequest,
    SentimentResponse,
    EntityExtractionRequest,
    EntityExtractionResponse,
    KeywordExtractionRequest,
    KeywordExtractionResponse,
    QuestionAnsweringRequest,
    QuestionAnsweringResponse
)
from ..dependencies import get_current_user, require_user
from ..exceptions import NotFoundException, BadRequestException

logger = get_logger(__name__)
router = APIRouter()


# NOTE: These functions would integrate with actual AI provider implementations
# For Phase 3, we're creating the API structure with placeholder implementations
# The actual AI integration will use existing scrapetui.py AI functions


def call_ai_provider(provider: str, prompt: str, content: str) -> str:
    """
    Call AI provider with prompt and content.
    Placeholder for actual AI integration.

    Args:
        provider: AI provider name (gemini, openai, claude)
        prompt: System prompt
        content: Content to analyze

    Returns:
        AI response text
    """
    # This would integrate with existing AI provider code
    # from scrapetui.py or new ai module
    return f"[{provider.upper()}] AI response for: {content[:100]}..."


def extract_entities_spacy(text: str) -> List[Dict[str, Any]]:
    """
    Extract entities using spaCy.
    Placeholder for actual NLP integration.

    Args:
        text: Text to analyze

    Returns:
        List of entities with type and text
    """
    # This would use spaCy integration from existing code
    return [
        {"text": "Example Entity", "type": "ORG"},
        {"text": "Another Entity", "type": "PERSON"}
    ]


def extract_keywords_tfidf(text: str, max_keywords: int = 10) -> List[Dict[str, Any]]:
    """
    Extract keywords using TF-IDF.
    Placeholder for actual keyword extraction.

    Args:
        text: Text to analyze
        max_keywords: Maximum number of keywords

    Returns:
        List of keywords with scores
    """
    # This would use existing keyword extraction code
    return [
        {"keyword": "example", "score": 0.95},
        {"keyword": "keyword", "score": 0.87}
    ]


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_article(
    request: SummarizeRequest,
    current_user: User = Depends(require_user)
):
    """
    Summarize article using AI.

    Args:
        request: Summarization request
        current_user: Current authenticated user

    Returns:
        Summary text

    Raises:
        NotFoundException: If article not found
    """
    try:
        with get_db_connection() as conn:
            # Get article
            row = conn.execute(
                "SELECT * FROM scraped_data WHERE id = ?",
                (request.article_id,)
            ).fetchone()

            if not row:
                raise NotFoundException(detail="Article not found")

            article = Article.from_db_row(row)

            # Check content exists
            if not article.content:
                raise BadRequestException(detail="Article has no content to summarize")

            # Generate summary based on style
            style_prompts = {
                "brief": "Provide a brief one-sentence summary:",
                "detailed": "Provide a detailed multi-paragraph summary:",
                "bullets": "Provide a bullet-point summary:",
                "technical": "Provide a technical summary with key terms:",
                "executive": "Provide an executive summary for decision-makers:"
            }

            prompt = style_prompts.get(request.style, style_prompts["brief"])

            # Call AI provider (placeholder implementation)
            summary = call_ai_provider(request.provider, prompt, article.content)

            # Update article with summary
            conn.execute(
                "UPDATE scraped_data SET summary = ? WHERE id = ?",
                (summary, article.id)
            )
            conn.commit()

            logger.info(
                f"Article {article.id} summarized by user {current_user.id} "
                f"(style={request.style}, provider={request.provider})"
            )

            return SummarizeResponse(
                summary=summary,
                style=request.style,
                provider=request.provider
            )

    except (NotFoundException, BadRequestException):
        raise
    except Exception as e:
        logger.error(f"Error summarizing article {request.article_id}: {e}")
        raise BadRequestException(detail="Failed to summarize article")


@router.post("/sentiment", response_model=SentimentResponse)
async def analyze_sentiment(
    request: SentimentRequest,
    current_user: User = Depends(require_user)
):
    """
    Analyze article sentiment using AI.

    Args:
        request: Sentiment analysis request
        current_user: Current authenticated user

    Returns:
        Sentiment classification

    Raises:
        NotFoundException: If article not found
    """
    try:
        with get_db_connection() as conn:
            # Get article
            row = conn.execute(
                "SELECT * FROM scraped_data WHERE id = ?",
                (request.article_id,)
            ).fetchone()

            if not row:
                raise NotFoundException(detail="Article not found")

            article = Article.from_db_row(row)

            # Check content exists
            if not article.content:
                raise BadRequestException(detail="Article has no content to analyze")

            # Analyze sentiment
            prompt = "Analyze the sentiment of this text. Respond with only one word: Positive, Negative, or Neutral."

            # Call AI provider (placeholder implementation)
            sentiment = call_ai_provider(request.provider, prompt, article.content)

            # Update article with sentiment
            conn.execute(
                "UPDATE scraped_data SET sentiment = ? WHERE id = ?",
                (sentiment, article.id)
            )
            conn.commit()

            logger.info(
                f"Sentiment analyzed for article {article.id} by user {current_user.id} "
                f"(provider={request.provider}, result={sentiment})"
            )

            return SentimentResponse(
                sentiment=sentiment,
                provider=request.provider
            )

    except (NotFoundException, BadRequestException):
        raise
    except Exception as e:
        logger.error(f"Error analyzing sentiment for article {request.article_id}: {e}")
        raise BadRequestException(detail="Failed to analyze sentiment")


@router.post("/entities", response_model=EntityExtractionResponse)
async def extract_entities(
    request: EntityExtractionRequest,
    current_user: User = Depends(require_user)
):
    """
    Extract named entities from article.

    Args:
        request: Entity extraction request
        current_user: Current authenticated user

    Returns:
        List of entities

    Raises:
        NotFoundException: If article not found
    """
    try:
        with get_db_connection() as conn:
            # Get article
            row = conn.execute(
                "SELECT * FROM scraped_data WHERE id = ?",
                (request.article_id,)
            ).fetchone()

            if not row:
                raise NotFoundException(detail="Article not found")

            article = Article.from_db_row(row)

            # Check content exists
            if not article.content:
                raise BadRequestException(detail="Article has no content to analyze")

            # Extract entities using spaCy (placeholder implementation)
            entities = extract_entities_spacy(article.content)

            logger.info(
                f"Entities extracted for article {article.id} by user {current_user.id} "
                f"(count={len(entities)})"
            )

            return EntityExtractionResponse(entities=entities)

    except (NotFoundException, BadRequestException):
        raise
    except Exception as e:
        logger.error(f"Error extracting entities for article {request.article_id}: {e}")
        raise BadRequestException(detail="Failed to extract entities")


@router.post("/keywords", response_model=KeywordExtractionResponse)
async def extract_keywords(
    request: KeywordExtractionRequest,
    current_user: User = Depends(require_user)
):
    """
    Extract keywords from article.

    Args:
        request: Keyword extraction request
        current_user: Current authenticated user

    Returns:
        List of keywords with scores

    Raises:
        NotFoundException: If article not found
    """
    try:
        with get_db_connection() as conn:
            # Get article
            row = conn.execute(
                "SELECT * FROM scraped_data WHERE id = ?",
                (request.article_id,)
            ).fetchone()

            if not row:
                raise NotFoundException(detail="Article not found")

            article = Article.from_db_row(row)

            # Check content exists
            if not article.content:
                raise BadRequestException(detail="Article has no content to analyze")

            # Extract keywords using TF-IDF (placeholder implementation)
            keywords = extract_keywords_tfidf(article.content, request.max_keywords)

            logger.info(
                f"Keywords extracted for article {article.id} by user {current_user.id} "
                f"(count={len(keywords)})"
            )

            return KeywordExtractionResponse(keywords=keywords)

    except (NotFoundException, BadRequestException):
        raise
    except Exception as e:
        logger.error(f"Error extracting keywords for article {request.article_id}: {e}")
        raise BadRequestException(detail="Failed to extract keywords")


@router.post("/qa", response_model=QuestionAnsweringResponse)
async def answer_question(
    request: QuestionAnsweringRequest,
    current_user: User = Depends(require_user)
):
    """
    Answer question using article content.

    Args:
        request: Question answering request
        current_user: Current authenticated user

    Returns:
        Answer with source article IDs

    Raises:
        BadRequestException: If no articles available
    """
    try:
        with get_db_connection() as conn:
            # Get articles to query
            if request.article_ids:
                # Use specified articles
                placeholders = ",".join(["?"] * len(request.article_ids))
                sql = f"SELECT * FROM scraped_data WHERE id IN ({placeholders})"
                rows = conn.execute(sql, request.article_ids).fetchall()
            else:
                # Use all user's articles (limit to recent 50)
                sql = """
                    SELECT * FROM scraped_data
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 50
                """
                rows = conn.execute(sql, (current_user.id,)).fetchall()

            if not rows:
                raise BadRequestException(detail="No articles available for question answering")

            # Combine article contents
            articles = [Article.from_db_row(row) for row in rows]
            combined_content = "\n\n".join([
                f"[Article {a.id}]: {a.content}"
                for a in articles if a.content
            ])

            if not combined_content:
                raise BadRequestException(detail="No article content available")

            # Answer question using AI (placeholder implementation)
            prompt = f"Based on the following articles, answer this question: {request.question}"
            answer = call_ai_provider(request.provider, prompt, combined_content)

            # Determine which articles were most relevant (simplified)
            source_ids = [a.id for a in articles[:3]]  # Use first 3 as sources

            logger.info(
                f"Question answered for user {current_user.id} "
                f"(provider={request.provider}, sources={len(source_ids)})"
            )

            return QuestionAnsweringResponse(
                answer=answer,
                sources=source_ids,
                provider=request.provider
            )

    except BadRequestException:
        raise
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise BadRequestException(detail="Failed to answer question")
