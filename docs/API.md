# WebScrape-TUI REST API Documentation

**Version**: v2.1.0-alpha.3  
**Base URL**: `http://localhost:8000`  
**Authentication**: JWT Bearer Token

## Quick Links
- Interactive Docs (Swagger): `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
- OpenAPI Spec: `http://localhost:8000/api/openapi.json`

## Overview

The WebScrape-TUI REST API provides comprehensive programmatic access to all features including web scraping, article management, AI analysis, and user administration.

**Key Features**:
- JWT authentication with access and refresh tokens
- Role-Based Access Control (Admin/User/Viewer)
- Rate limiting (60 requests/minute default)
- Article CRUD with pagination and filtering
- Web scraping with built-in and custom scrapers
- AI-powered summarization, sentiment, entities, keywords, Q&A
- Admin user management

## Authentication

All protected endpoints require JWT Bearer token in Authorization header:
```
Authorization: Bearer <access_token>
```

### Login Flow
1. POST /api/auth/login → Get access + refresh tokens
2. Use access token for API requests (30 min expiry)
3. POST /api/auth/refresh → Get new tokens when expired
4. POST /api/auth/logout → Invalidate tokens

**Example Login**:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Ch4ng3M3"}'
```

## Endpoints Summary

### Authentication
- `POST /api/auth/login` - Login and get JWT tokens
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/logout` - Logout

### Articles
- `GET /api/articles` - List articles (paginated, filtered)
- `GET /api/articles/{id}` - Get single article
- `POST /api/articles` - Create article
- `PUT /api/articles/{id}` - Update article (owner/admin)
- `DELETE /api/articles/{id}` - Delete article (owner/admin)

### Scrapers
- `GET /api/scrapers/available` - List available scrapers
- `GET /api/scrapers/profiles` - List scraper profiles
- `POST /api/scrapers/profiles` - Create scraper profile
- `PUT /api/scrapers/profiles/{id}` - Update profile (owner/admin)
- `DELETE /api/scrapers/profiles/{id}` - Delete profile (owner/admin)
- `POST /api/scrapers/scrape` - Scrape URL

### Users (Admin Only)
- `GET /api/users` - List all users
- `GET /api/users/{id}` - Get user
- `POST /api/users` - Create user
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user
- `PUT /api/users/{id}/password` - Change password (own account)

### Tags
- `GET /api/tags` - List tags with counts
- `POST /api/tags` - Create tag
- `DELETE /api/tags/{id}` - Delete tag
- `GET /api/tags/{id}/articles` - Get articles by tag

### AI
- `POST /api/ai/summarize` - Summarize article (5 styles)
- `POST /api/ai/sentiment` - Analyze sentiment
- `POST /api/ai/entities` - Extract named entities
- `POST /api/ai/keywords` - Extract keywords (TF-IDF)
- `POST /api/ai/qa` - Question answering

## Example Usage

### Python Client
```python
import requests

BASE = "http://localhost:8000"

# Login
r = requests.post(f"{BASE}/api/auth/login", json={
    "username": "admin", "password": "Ch4ng3M3"
})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# List articles
articles = requests.get(f"{BASE}/api/articles", headers=headers).json()

# Scrape URL
result = requests.post(
    f"{BASE}/api/scrapers/scrape",
    headers=headers,
    json={
        "url": "https://example.com/article",
        "scraper_name": "Generic HTML",
        "tags": ["test"]
    }
).json()

# Summarize
summary = requests.post(
    f"{BASE}/api/ai/summarize",
    headers=headers,
    json={"article_id": result["article"]["id"], "style": "brief", "provider": "gemini"}
).json()
```

### cURL Examples
```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Ch4ng3M3"}'

# List articles (with token)
curl http://localhost:8000/api/articles \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Create article
curl -X POST http://localhost:8000/api/articles \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","title":"Test","content":"Content","link":"https://example.com"}'
```

## Rate Limiting

Every response includes rate limit headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1696348800
```

When limit exceeded (429):
```json
{
  "detail": "Rate limit exceeded. Max 60 requests per 60 seconds.",
  "retry_after": 60
}
```

## Error Responses

All errors follow consistent format:
```json
{
  "detail": "Error message",
  "type": "ErrorType"
}
```

**Status Codes**:
- 200: Success (GET/PUT)
- 201: Created (POST)
- 204: No Content (DELETE)
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 409: Conflict
- 422: Validation Error
- 429: Rate Limit Exceeded
- 500: Internal Server Error

## Running the API

### Development
```bash
python -m scrapetui.api.app
# Or: uvicorn scrapetui.api.app:app --reload
```

### Production
```bash
gunicorn scrapetui.api.app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Environment Configuration
Create `.env`:
```bash
API_HOST=0.0.0.0
API_PORT=8000
API_JWT_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")
API_RATE_LIMIT_PER_MINUTE=60
GEMINI_API_KEY=your_key
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
```

## Full Endpoint Reference

See interactive documentation at `http://localhost:8000/api/docs` for complete request/response schemas, examples, and try-it-out functionality.

**Last Updated**: October 3, 2025  
**Contact**: https://github.com/doublegate/WebScrape-TUI
