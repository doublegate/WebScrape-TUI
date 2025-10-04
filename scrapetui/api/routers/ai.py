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
    QuestionAnsweringResponse,
    EntityRelationshipsRequest,
    EntityRelationshipsResponse,
    SummaryQualityRequest,
    SummaryQualityResponse,
    ContentSimilarityRequest,
    ContentSimilarityResponse,
    TopicModelingRequest,
    TopicModelingResponse
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

    Args:
        text: Text to analyze

    Returns:
        List of entities with type and text
    """
    from ...ai.processors import extract_named_entities

    # Extract entities using real spaCy implementation
    entities = extract_named_entities(text)

    # Convert format from {'text', 'label', 'start', 'end'} to {'text', 'type'}
    return [
        {"text": ent['text'], "type": ent['label']}
        for ent in entities
    ]


def extract_keywords_tfidf(text: str, max_keywords: int = 10) -> List[Dict[str, Any]]:
    """
    Extract keywords using TF-IDF.

    Args:
        text: Text to analyze
        max_keywords: Maximum number of keywords

    Returns:
        List of keywords with scores
    """
    from ...ai.processors import extract_keywords

    # Extract keywords using real TF-IDF implementation
    return extract_keywords(text, top_n=max_keywords)


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


# === Sprint 3: Advanced AI Endpoints ===


@router.post("/entity-relationships", response_model=EntityRelationshipsResponse)
async def extract_entity_relationships(
    request: EntityRelationshipsRequest,
    current_user: User = Depends(require_user)
):
    """
    Extract entity relationships and build knowledge graph.

    Args:
        request: Entity relationships request
        current_user: Current authenticated user

    Returns:
        Entities, relationships, and knowledge graph

    Raises:
        BadRequestException: If no articles available
    """
    try:
        from ...ai.entity_relationships import (
            extract_relationships_from_articles,
            build_knowledge_graph
        )

        # Get articles
        with get_db_connection() as conn:
            if not request.article_ids:
                raise BadRequestException(detail="Article IDs are required")

            placeholders = ",".join(["?"] * len(request.article_ids))
            sql = f"SELECT * FROM scraped_data WHERE id IN ({placeholders})"
            rows = conn.execute(sql, request.article_ids).fetchall()

            if not rows:
                raise BadRequestException(detail="No articles found")

            articles = [Article.from_db_row(row) for row in rows]

        # Extract relationships
        result = extract_relationships_from_articles(
            request.article_ids,
            entity_types=request.entity_types
        )

        # Build knowledge graph
        graph = build_knowledge_graph(result['relationships'])

        logger.info(
            f"Entity relationships extracted by user {current_user.id} "
            f"(articles={len(request.article_ids)}, entities={len(result['entities'])})"
        )

        return EntityRelationshipsResponse(
            entities=result['entities'],
            relationships=result['relationships'],
            knowledge_graph=graph
        )

    except BadRequestException:
        raise
    except Exception as e:
        logger.error(f"Error extracting entity relationships: {e}")
        raise BadRequestException(detail="Failed to extract entity relationships")


@router.post("/summary-quality", response_model=SummaryQualityResponse)
async def evaluate_summary_quality(
    request: SummaryQualityRequest,
    current_user: User = Depends(require_user)
):
    """
    Evaluate summary quality using ROUGE and coherence metrics.

    Args:
        request: Summary quality request
        current_user: Current authenticated user

    Returns:
        Quality scores (ROUGE-1, ROUGE-2, ROUGE-L, coherence, coverage, overall)

    Raises:
        NotFoundException: If article not found
        BadRequestException: If article has no summary
    """
    try:
        from ...ai.summary_quality import evaluate_summary_quality as eval_quality

        with get_db_connection() as conn:
            # Get article
            row = conn.execute(
                "SELECT * FROM scraped_data WHERE id = ?",
                (request.article_id,)
            ).fetchone()

            if not row:
                raise NotFoundException(detail="Article not found")

            article = Article.from_db_row(row)

            # Check content and summary exist
            if not article.content:
                raise BadRequestException(detail="Article has no content")

            if not article.summary and not request.generate_if_missing:
                raise BadRequestException(
                    detail="Article has no summary. Set generate_if_missing=true to create one."
                )

            # Generate summary if requested and missing
            if not article.summary and request.generate_if_missing:
                # Generate a brief summary
                prompt = "Provide a brief one-sentence summary:"
                summary = call_ai_provider("gemini", prompt, article.content)

                # Update article
                conn.execute(
                    "UPDATE scraped_data SET summary = ? WHERE id = ?",
                    (summary, article.id)
                )
                conn.commit()
                article.summary = summary

        # Evaluate summary quality
        metrics = eval_quality(article.content, article.summary)

        logger.info(
            f"Summary quality evaluated for article {article.id} by user {current_user.id} "
            f"(overall={metrics['overall']:.2f})"
        )

        return SummaryQualityResponse(
            rouge_1=metrics['rouge_1'],
            rouge_2=metrics['rouge_2'],
            rouge_l=metrics['rouge_l'],
            coherence_score=metrics['coherence'],
            coverage_score=metrics['coverage'],
            overall_score=metrics['overall']
        )

    except (NotFoundException, BadRequestException):
        raise
    except Exception as e:
        logger.error(f"Error evaluating summary quality for article {request.article_id}: {e}")
        raise BadRequestException(detail="Failed to evaluate summary quality")


@router.post("/content-similarity", response_model=ContentSimilarityResponse)
async def find_similar_content(
    request: ContentSimilarityRequest,
    current_user: User = Depends(require_user)
):
    """
    Find similar articles using content similarity.

    Args:
        request: Content similarity request
        current_user: Current authenticated user

    Returns:
        List of similar articles with similarity scores

    Raises:
        NotFoundException: If article not found
    """
    try:
        from ...ai.content_similarity import find_similar_articles

        with get_db_connection() as conn:
            # Get article
            row = conn.execute(
                "SELECT * FROM scraped_data WHERE id = ?",
                (request.article_id,)
            ).fetchone()

            if not row:
                raise NotFoundException(detail="Article not found")

            article = Article.from_db_row(row)

            if not article.content:
                raise BadRequestException(detail="Article has no content")

        # Find similar articles
        similar = find_similar_articles(
            request.article_id,
            top_k=request.top_k,
            threshold=request.threshold
        )

        logger.info(
            f"Similar articles found for article {request.article_id} by user {current_user.id} "
            f"(found={len(similar)})"
        )

        return ContentSimilarityResponse(similar_articles=similar)

    except (NotFoundException, BadRequestException):
        raise
    except Exception as e:
        logger.error(f"Error finding similar content for article {request.article_id}: {e}")
        raise BadRequestException(detail="Failed to find similar content")


@router.post("/topic-modeling", response_model=TopicModelingResponse)
async def discover_topics(
    request: TopicModelingRequest,
    current_user: User = Depends(require_user)
):
    """
    Discover topics using LDA or NMF topic modeling.

    Args:
        request: Topic modeling request
        current_user: Current authenticated user

    Returns:
        Topics with top words and article-topic assignments

    Raises:
        BadRequestException: If no articles available
    """
    try:
        from ...ai.topic_modeling import discover_topics as discover

        with get_db_connection() as conn:
            # Get articles
            if request.article_ids:
                placeholders = ",".join(["?"] * len(request.article_ids))
                sql = f"SELECT * FROM scraped_data WHERE id IN ({placeholders})"
                rows = conn.execute(sql, request.article_ids).fetchall()
            else:
                # Use all user's articles (limit to recent 100)
                sql = """
                    SELECT * FROM scraped_data
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 100
                """
                rows = conn.execute(sql, (current_user.id,)).fetchall()

            if not rows:
                raise BadRequestException(detail="No articles available for topic modeling")

            article_ids = [row[0] for row in rows]

        # Discover topics
        result = discover(
            article_ids=article_ids,
            num_topics=request.num_topics,
            algorithm=request.algorithm,
            words_per_topic=request.words_per_topic
        )

        logger.info(
            f"Topics discovered by user {current_user.id} "
            f"(articles={len(article_ids)}, topics={request.num_topics}, algorithm={request.algorithm})"
        )

        return TopicModelingResponse(
            topics=result['topics'],
            article_topics=result['article_topics']
        )

    except BadRequestException:
        raise
    except Exception as e:
        logger.error(f"Error discovering topics: {e}")
        raise BadRequestException(detail="Failed to discover topics")
