"""Tests for AI endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_summarize_article(client: TestClient, user_auth_headers: dict, sample_article: int):
    """Test article summarization."""
    response = client.post(
        "/api/ai/summarize",
        headers=user_auth_headers,
        json={
            "article_id": sample_article,
            "style": "brief",
            "provider": "gemini"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert data["style"] == "brief"
    assert data["provider"] == "gemini"


def test_summarize_article_not_found(client: TestClient, user_auth_headers: dict):
    """Test summarizing non-existent article."""
    response = client.post(
        "/api/ai/summarize",
        headers=user_auth_headers,
        json={
            "article_id": 99999,
            "style": "brief",
            "provider": "gemini"
        }
    )

    assert response.status_code == 404


def test_summarize_different_styles(client: TestClient, user_auth_headers: dict, sample_article: int):
    """Test different summarization styles."""
    for style in ["brief", "detailed", "bullets", "technical", "executive"]:
        response = client.post(
            "/api/ai/summarize",
            headers=user_auth_headers,
            json={
                "article_id": sample_article,
                "style": style,
                "provider": "gemini"
            }
        )

        assert response.status_code == 200
        assert response.json()["style"] == style


def test_analyze_sentiment(client: TestClient, user_auth_headers: dict, sample_article: int):
    """Test sentiment analysis."""
    response = client.post(
        "/api/ai/sentiment",
        headers=user_auth_headers,
        json={
            "article_id": sample_article,
            "provider": "gemini"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "sentiment" in data
    assert data["provider"] == "gemini"


def test_extract_entities(client: TestClient, user_auth_headers: dict, sample_article: int):
    """Test entity extraction."""
    response = client.post(
        "/api/ai/entities",
        headers=user_auth_headers,
        json={"article_id": sample_article}
    )

    assert response.status_code == 200
    data = response.json()
    assert "entities" in data
    assert isinstance(data["entities"], list)


def test_extract_keywords(client: TestClient, user_auth_headers: dict, sample_article: int):
    """Test keyword extraction."""
    response = client.post(
        "/api/ai/keywords",
        headers=user_auth_headers,
        json={
            "article_id": sample_article,
            "max_keywords": 5
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "keywords" in data
    assert isinstance(data["keywords"], list)
    assert len(data["keywords"]) <= 5


def test_answer_question(client: TestClient, user_auth_headers: dict, sample_article: int):
    """Test question answering."""
    response = client.post(
        "/api/ai/qa",
        headers=user_auth_headers,
        json={
            "question": "What is this article about?",
            "article_ids": [sample_article],
            "provider": "gemini"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert isinstance(data["sources"], list)


def test_answer_question_no_articles(client: TestClient, user_auth_headers: dict):
    """Test question answering with no articles specified."""
    # User has no articles yet
    response = client.post(
        "/api/ai/qa",
        headers=user_auth_headers,
        json={
            "question": "What is this about?",
            "provider": "gemini"
        }
    )

    # Should return error if no articles available
    assert response.status_code in [200, 400]  # May succeed if using admin's articles


def test_extract_keywords_custom_limit(client: TestClient, user_auth_headers: dict, sample_article: int):
    """Test keyword extraction with custom limit."""
    response = client.post(
        "/api/ai/keywords",
        headers=user_auth_headers,
        json={
            "article_id": sample_article,
            "max_keywords": 15
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["keywords"]) <= 15
