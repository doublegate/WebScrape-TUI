# v2.2.0 Security API Testing Guide

**Date**: 2025-11-18
**API Version**: v1
**Endpoints**: 13 security endpoints
**Status**: Ready for Testing

---

## Quick Start

### 1. Install Dependencies

```bash
pip install fastapi uvicorn pydantic
```

### 2. Start API Server

```bash
uvicorn scrapetui.api.app:app --reload --port 8000
```

### 3. Access Swagger UI

Navigate to: http://localhost:8000/docs

All 13 security endpoints will be listed under the "security" tag.

---

## API Endpoints Overview

### Authentication (2 endpoints)

#### POST `/api/v1/security/login`
**Purpose**: Enhanced login with rate limiting and audit logging

**Request Body**:
```json
{
  "username": "admin",
  "password": "AdminP@ss123"
}
```

**Response** (Success):
```json
{
  "success": true,
  "user_id": 1,
  "session_token": "64-character-hex-token",
  "message": "Authentication successful",
  "user_role": "admin"
}
```

**Response** (Failure):
```json
{
  "success": false,
  "message": "Invalid credentials or account locked"
}
```

**Testing with curl**:
```bash
curl -X POST http://localhost:8000/api/v1/security/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"AdminP@ss123"}'
```

---

#### POST `/api/v1/security/logout`
**Purpose**: Log out current user and invalidate session

**Headers**:
```
Authorization: Bearer <session_token>
```

**Response**:
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

**Testing with curl**:
```bash
curl -X POST http://localhost:8000/api/v1/security/logout \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"
```

---

### Password Management (4 endpoints)

#### POST `/api/v1/security/password/validate`
**Purpose**: Validate password against policy requirements

**Request Body**:
```json
{
  "password": "Str0ng!P@ssw0rd",
  "username": "testuser"
}
```

**Response**:
```json
{
  "is_valid": true,
  "score": 85,
  "strength_level": "very_strong",
  "errors": [],
  "warnings": []
}
```

**Testing with curl**:
```bash
curl -X POST http://localhost:8000/api/v1/security/password/validate \
  -H "Content-Type: application/json" \
  -d '{"password":"Str0ng!P@ssw0rd","username":"testuser"}'
```

---

#### POST `/api/v1/security/password/change`
**Purpose**: Change user password with policy validation

**Headers**:
```
Authorization: Bearer <session_token>
```

**Request Body**:
```json
{
  "old_password": "OldP@ss123",
  "new_password": "N3wP@ssw0rd!"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

---

#### POST `/api/v1/security/password/reset/generate` (Admin Only)
**Purpose**: Generate password reset token

**Headers**:
```
Authorization: Bearer <admin_session_token>
```

**Request Body**:
```json
{
  "username": "testuser"
}
```

**Response**:
```json
{
  "token": "64-character-hex-token",
  "expires_at": "2025-11-19T14:00:00+00:00",
  "username": "testuser"
}
```

---

#### POST `/api/v1/security/password/reset/use`
**Purpose**: Use reset token to set new password

**Request Body**:
```json
{
  "token": "64-character-hex-token",
  "new_password": "N3wP@ssw0rd!"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Password reset successfully"
}
```

---

### Account Management (3 endpoints)

#### GET `/api/v1/security/account/status`
**Purpose**: Get security status for current user

**Headers**:
```
Authorization: Bearer <session_token>
```

**Response**:
```json
{
  "username": "testuser",
  "is_active": true,
  "account_locked": false,
  "locked_until": null,
  "failed_login_attempts": 0,
  "last_failed_login": null,
  "password_changed_at": "2025-11-18T10:00:00+00:00",
  "force_password_change": false,
  "last_login": "2025-11-18T14:00:00+00:00"
}
```

---

#### POST `/api/v1/security/account/{username}/lock` (Admin Only)
**Purpose**: Lock user account

**Headers**:
```
Authorization: Bearer <admin_session_token>
```

**Path Parameters**:
- `username`: Username to lock

**Response**:
```json
{
  "success": true,
  "message": "Account 'testuser' locked"
}
```

---

#### POST `/api/v1/security/account/{username}/unlock` (Admin Only)
**Purpose**: Unlock user account

**Headers**:
```
Authorization: Bearer <admin_session_token>
```

**Path Parameters**:
- `username`: Username to unlock

**Response**:
```json
{
  "success": true,
  "message": "Account 'testuser' unlocked"
}
```

---

### Quota Management (2 endpoints)

#### GET `/api/v1/security/quotas`
**Purpose**: Get quota status for current user

**Headers**:
```
Authorization: Bearer <session_token>
```

**Response**:
```json
{
  "articles": {
    "quota_type": "articles",
    "current_usage": 42,
    "quota_limit": 10000,
    "remaining": 9958,
    "percentage_used": 0.42,
    "exceeded": false
  },
  "scrapers": {
    "quota_type": "scrapers",
    "current_usage": 5,
    "quota_limit": 100,
    "remaining": 95,
    "percentage_used": 5.0,
    "exceeded": false
  }
}
```

---

#### POST `/api/v1/security/quotas/set` (Admin Only)
**Purpose**: Set user quotas

**Headers**:
```
Authorization: Bearer <admin_session_token>
```

**Request Body**:
```json
{
  "username": "testuser",
  "article_quota": 5000,
  "scraper_quota": 50
}
```

**Response**:
```json
{
  "success": true,
  "message": "Quotas updated for 'testuser'"
}
```

---

### Audit Log Management (3 endpoints)

#### GET `/api/v1/security/audit/logs` (Admin Only)
**Purpose**: Get audit log entries with filtering

**Headers**:
```
Authorization: Bearer <admin_session_token>
```

**Query Parameters**:
- `event_type` (optional): Filter by event type (e.g., "login_success")
- `username` (optional): Filter by username
- `since` (optional): ISO format datetime (e.g., "2025-11-18T00:00:00")
- `limit` (optional): Max entries to return (default: 50, max: 1000)

**Response**:
```json
{
  "events": [
    {
      "id": 1,
      "event_type": "login_success",
      "user_id": 1,
      "username": "admin",
      "ip_address": "127.0.0.1",
      "user_agent": "Mozilla/5.0...",
      "event_data": {"browser": "Chrome"},
      "created_at": "2025-11-18T14:00:00+00:00"
    }
  ],
  "total_count": 1
}
```

**Testing with curl**:
```bash
curl -X GET "http://localhost:8000/api/v1/security/audit/logs?limit=10" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

#### GET `/api/v1/security/audit/stats` (Admin Only)
**Purpose**: Get audit log statistics

**Headers**:
```
Authorization: Bearer <admin_session_token>
```

**Response**:
```json
{
  "total_events": 152,
  "by_event_type": {
    "login_success": 45,
    "login_failure": 12,
    "password_changed": 8,
    "account_locked": 3
  },
  "by_user": {
    "admin": 67,
    "testuser": 85
  }
}
```

---

#### DELETE `/api/v1/security/audit/cleanup` (Admin Only)
**Purpose**: Clean up old audit log entries

**Headers**:
```
Authorization: Bearer <admin_session_token>
```

**Query Parameters**:
- `days`: Number of days to retain (default: 90)

**Response**:
```json
{
  "success": true,
  "message": "Deleted 23 audit log entries older than 90 days"
}
```

---

## Testing Scenarios

### Scenario 1: User Login Flow

1. **Validate password** (before registration):
   ```bash
   POST /api/v1/security/password/validate
   {"password": "NewUs3r!P@ss", "username": "newuser"}
   ```

2. **Create user** (via standard API, not security endpoint)

3. **Login**:
   ```bash
   POST /api/v1/security/login
   {"username": "newuser", "password": "NewUs3r!P@ss"}
   ```

4. **Get account status**:
   ```bash
   GET /api/v1/security/account/status
   Authorization: Bearer <token_from_login>
   ```

5. **Check quotas**:
   ```bash
   GET /api/v1/security/quotas
   Authorization: Bearer <token_from_login>
   ```

---

### Scenario 2: Password Change Flow

1. **Login** to get session token

2. **Change password**:
   ```bash
   POST /api/v1/security/password/change
   Authorization: Bearer <token>
   {
     "old_password": "OldP@ss123",
     "new_password": "N3wP@ssw0rd!"
   }
   ```

3. **Login again** with new password (old session invalidated)

---

### Scenario 3: Admin Password Reset

1. **Admin generates reset token**:
   ```bash
   POST /api/v1/security/password/reset/generate
   Authorization: Bearer <admin_token>
   {"username": "forgetful_user"}
   ```

2. **User uses token to reset**:
   ```bash
   POST /api/v1/security/password/reset/use
   {"token": "64-char-token", "new_password": "N3wP@ssw0rd!"}
   ```

3. **User logs in** with new password

---

### Scenario 4: Account Lockout

1. **Make 5 failed login attempts**:
   ```bash
   # Repeat 5 times
   POST /api/v1/security/login
   {"username": "testuser", "password": "WrongPassword"}
   ```

2. **6th attempt fails with lockout message**

3. **Admin unlocks account**:
   ```bash
   POST /api/v1/security/account/testuser/unlock
   Authorization: Bearer <admin_token>
   ```

4. **User can login again**

---

### Scenario 5: Quota Management

1. **Admin checks user quota**:
   ```bash
   GET /api/v1/security/quotas
   Authorization: Bearer <user_token>
   ```

2. **Admin adjusts quota**:
   ```bash
   POST /api/v1/security/quotas/set
   Authorization: Bearer <admin_token>
   {
     "username": "testuser",
     "article_quota": 20000,
     "scraper_quota": 200
   }
   ```

3. **User verifies new quota**

---

### Scenario 6: Audit Log Review

1. **Admin views recent events**:
   ```bash
   GET /api/v1/security/audit/logs?limit=50
   Authorization: Bearer <admin_token>
   ```

2. **Admin filters by event type**:
   ```bash
   GET /api/v1/security/audit/logs?event_type=login_failure
   Authorization: Bearer <admin_token>
   ```

3. **Admin gets statistics**:
   ```bash
   GET /api/v1/security/audit/stats
   Authorization: Bearer <admin_token>
   ```

4. **Admin cleans old logs**:
   ```bash
   DELETE /api/v1/security/audit/cleanup?days=90
   Authorization: Bearer <admin_token>
   ```

---

## Error Responses

### 401 Unauthorized
**Cause**: Missing or invalid session token

**Response**:
```json
{
  "detail": "Missing or invalid authorization header"
}
```

### 403 Forbidden
**Cause**: Insufficient permissions (non-admin accessing admin endpoint)

**Response**:
```json
{
  "detail": "Administrator privileges required"
}
```

### 400 Bad Request
**Cause**: Invalid request data

**Response**:
```json
{
  "detail": "Password does not meet requirements: Password must be at least 12 characters long"
}
```

### 404 Not Found
**Cause**: User not found

**Response**:
```json
{
  "detail": "User 'nonexistent' not found"
}
```

---

## Rate Limiting

All endpoints are subject to rate limiting:
- Standard endpoints: 100 requests/minute
- AI endpoints: 10 requests/minute

Exceeding rate limits returns:
```json
{
  "detail": "Rate limit exceeded. Try again in X seconds."
}
```

---

## Authentication

Most endpoints require authentication via Bearer token:

1. **Get token** via login endpoint
2. **Include in headers**:
   ```
   Authorization: Bearer <64-character-hex-token>
   ```
3. **Token expires** after 24 hours

---

## Testing Checklist

### Basic Functionality
- [ ] Login with valid credentials
- [ ] Login with invalid credentials
- [ ] Validate strong password
- [ ] Validate weak password
- [ ] Change password successfully
- [ ] Get account status
- [ ] Get quota status

### Admin Functions
- [ ] Generate password reset token
- [ ] Lock user account
- [ ] Unlock user account
- [ ] Set user quotas
- [ ] View audit logs
- [ ] Filter audit logs
- [ ] Get audit statistics
- [ ] Clean up old audit logs

### Security Features
- [ ] Rate limiting triggers after 5 failed attempts
- [ ] Account locks automatically
- [ ] Password policy enforced
- [ ] Audit events logged
- [ ] Session invalidates on password change

### Error Handling
- [ ] 401 on missing token
- [ ] 403 on insufficient permissions
- [ ] 400 on invalid input
- [ ] 404 on nonexistent user

---

## Performance Benchmarks

Expected response times (approximate):

| Endpoint | Expected Time |
|----------|---------------|
| /login | ~100ms (bcrypt hashing) |
| /password/validate | <1ms |
| /password/change | ~100ms (bcrypt hashing) |
| /account/status | <5ms |
| /quotas | <5ms |
| /audit/logs | <10ms (depends on limit) |
| /audit/stats | <20ms (aggregation) |

---

## Integration with Main API

The security router is already integrated into the main FastAPI app:

```python
# scrapetui/api/app.py
from . import auth, security

app.include_router(security.router)  # Security router has its own prefix
```

All endpoints are available at:
- Base URL: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Next Steps

1. **Start API server**: `uvicorn scrapetui.api.app:app --reload`
2. **Open Swagger UI**: http://localhost:8000/docs
3. **Test each endpoint** using the interactive documentation
4. **Run automated tests**: `pytest tests/api/`
5. **Benchmark performance** under load

---

## Support

For issues or questions:
- Check API logs for detailed error messages
- Review `scrapetui/api/security.py` for endpoint implementations
- See `docs/V2.2.0_COMPLETE_SUMMARY.md` for architecture details

---

**Document Version**: 1.0
**Last Updated**: 2025-11-18
**Status**: Ready for Testing
