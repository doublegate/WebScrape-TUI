"""Pydantic models for API request/response validation."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, ConfigDict


# === Authentication Models ===

class Token(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Refresh token request."""
    refresh_token: str


class UserLogin(BaseModel):
    """User login request."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


# === User Models ===

class UserBase(BaseModel):
    """Base user model."""
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    role: str = Field(default="user", pattern="^(admin|user|viewer)$")


class UserCreate(UserBase):
    """User creation request."""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """User update request."""
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, pattern="^(admin|user|viewer)$")
    is_active: Optional[bool] = None


class UserPasswordChange(BaseModel):
    """Password change request."""
    old_password: str
    new_password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    """User response model."""
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# === Article Models ===

class ArticleBase(BaseModel):
    """Base article model."""
    url: str = Field(..., max_length=500)
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    link: str = Field(..., max_length=500)


class ArticleCreate(ArticleBase):
    """Article creation request (manual entry or scraping result)."""
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    tags: Optional[List[str]] = None


class ArticleUpdate(BaseModel):
    """Article update request."""
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    tags: Optional[List[str]] = None


class ArticleResponse(ArticleBase):
    """Article response model."""
    id: int
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    timestamp: datetime
    user_id: int
    tags: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


class ArticleListResponse(BaseModel):
    """Paginated article list response."""
    articles: List[ArticleResponse]
    total: int
    page: int
    page_size: int
    pages: int


# === Scraper Models ===

class ScraperProfileBase(BaseModel):
    """Base scraper profile model."""
    name: str = Field(..., max_length=100)
    url: str = Field(..., max_length=500)
    selector: str = Field(..., max_length=200)
    default_limit: int = Field(default=0, ge=0, le=100)
    default_tags_csv: Optional[str] = None
    description: Optional[str] = None


class ScraperProfileCreate(ScraperProfileBase):
    """Scraper profile creation request."""
    is_shared: bool = False


class ScraperProfileUpdate(BaseModel):
    """Scraper profile update request."""
    url: Optional[str] = Field(None, max_length=500)
    selector: Optional[str] = Field(None, max_length=200)
    default_limit: Optional[int] = Field(None, ge=0, le=100)
    default_tags_csv: Optional[str] = None
    description: Optional[str] = None
    is_shared: Optional[bool] = None


class ScraperProfileResponse(ScraperProfileBase):
    """Scraper profile response model."""
    id: int
    is_preinstalled: bool
    user_id: int
    is_shared: bool

    model_config = ConfigDict(from_attributes=True)


class ScrapeRequest(BaseModel):
    """Scraping request."""
    url: str = Field(..., max_length=500)
    scraper_name: Optional[str] = None
    tags: Optional[List[str]] = None
    auto_summarize: bool = False


class ScrapeResult(BaseModel):
    """Scraping result response."""
    success: bool
    article: Optional[ArticleResponse] = None
    error: Optional[str] = None


# === Tag Models ===

class TagBase(BaseModel):
    """Base tag model."""
    name: str = Field(..., max_length=50)


class TagCreate(TagBase):
    """Tag creation request."""


class TagResponse(TagBase):
    """Tag response model."""
    id: int
    article_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# === AI Models ===

class SummarizeRequest(BaseModel):
    """Summarization request."""
    article_id: int
    style: str = Field(default="brief", pattern="^(brief|detailed|bullets|technical|executive)$")
    provider: str = Field(default="gemini", pattern="^(gemini|openai|claude)$")


class SummarizeResponse(BaseModel):
    """Summarization response."""
    summary: str
    style: str
    provider: str


class SentimentRequest(BaseModel):
    """Sentiment analysis request."""
    article_id: int
    provider: str = Field(default="gemini", pattern="^(gemini|openai|claude)$")


class SentimentResponse(BaseModel):
    """Sentiment analysis response."""
    sentiment: str
    provider: str


class EntityExtractionRequest(BaseModel):
    """Entity extraction request."""
    article_id: int


class EntityExtractionResponse(BaseModel):
    """Entity extraction response."""
    entities: List[dict]


class KeywordExtractionRequest(BaseModel):
    """Keyword extraction request."""
    article_id: int
    max_keywords: int = Field(default=10, ge=1, le=50)


class KeywordExtractionResponse(BaseModel):
    """Keyword extraction response."""
    keywords: List[dict]


class QuestionAnsweringRequest(BaseModel):
    """Question answering request."""
    question: str = Field(..., max_length=500)
    article_ids: Optional[List[int]] = None
    provider: str = Field(default="gemini", pattern="^(gemini|openai|claude)$")


class QuestionAnsweringResponse(BaseModel):
    """Question answering response."""
    answer: str
    sources: List[int]
    provider: str


# === Search/Filter Models ===

class ArticleSearchRequest(BaseModel):
    """Article search request."""
    query: Optional[str] = None
    tags: Optional[List[str]] = None
    sentiment: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    user_id: Optional[int] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="date_desc")


# === Advanced AI Models (Sprint 3) ===

class EntityRelationshipsRequest(BaseModel):
    """Entity relationships extraction request."""
    article_ids: List[int] = Field(..., min_items=1)
    entity_types: Optional[List[str]] = None
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class EntityRelationshipsResponse(BaseModel):
    """Entity relationships extraction response."""
    entities: List[dict]
    relationships: List[dict]
    knowledge_graph: dict


class SummaryQualityRequest(BaseModel):
    """Summary quality evaluation request."""
    article_id: int
    generate_if_missing: bool = False


class SummaryQualityResponse(BaseModel):
    """Summary quality evaluation response."""
    rouge_1: float
    rouge_2: float
    rouge_l: float
    coherence_score: float
    coverage_score: float
    overall_score: float


class ContentSimilarityRequest(BaseModel):
    """Content similarity search request."""
    article_id: int
    top_k: int = Field(default=5, ge=1, le=20)
    threshold: float = Field(default=0.3, ge=0.0, le=1.0)


class ContentSimilarityResponse(BaseModel):
    """Content similarity search response."""
    similar_articles: List[dict]


class TopicModelingRequest(BaseModel):
    """Topic modeling request."""
    article_ids: Optional[List[int]] = None
    num_topics: int = Field(default=5, ge=2, le=20)
    algorithm: str = Field(default="lda", pattern="^(lda|nmf)$")
    words_per_topic: int = Field(default=10, ge=5, le=20)


class TopicModelingResponse(BaseModel):
    """Topic modeling response."""
    topics: List[dict]
    article_topics: dict


# === User Profile Models (Sprint 3) ===

class UserProfileResponse(BaseModel):
    """User profile response (for current user)."""
    id: int
    username: str
    email: Optional[EmailStr] = None
    role: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool
    article_count: int
    scraper_count: int

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    """User profile update request (for current user)."""
    email: Optional[EmailStr] = None


class UserSessionResponse(BaseModel):
    """User session response."""
    id: int
    created_at: datetime
    expires_at: datetime
    is_current: bool

    model_config = ConfigDict(from_attributes=True)


# === Error Models ===

class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str
    type: Optional[str] = None
