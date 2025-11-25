# API Contract: Retext SMS Search

**Date**: 2025-11-24
**Feature**: 001-sms-search

## Overview

Simple REST API served by Flask. All endpoints require authentication via
session cookie except `/login` and `/health`.

**Base URL**: `http://localhost:5000` (or via Cloudflare Tunnel)

## Authentication

### POST /login

Authenticate with shared password.

**Request**:
```
Content-Type: application/x-www-form-urlencoded

password=<user_password>
```

**Response (success)**: `302 Redirect to /`
- Sets session cookie with `HttpOnly`, `SameSite=Strict` flags

**Response (failure)**: `302 Redirect to /login?error=1`

### POST /logout

Clear session and log out.

**Response**: `302 Redirect to /login`

---

## Pages (HTML)

### GET /

Landing page with search interface.

**Requires**: Authentication (redirects to `/login` if not authenticated)

**Response**: `200 OK`
- HTML page with:
  - Total message count (FR-008)
  - Search input (FR-009)
  - Results area

### GET /login

Login form page.

**Response**: `200 OK`
- HTML login form

---

## API Endpoints (JSON)

### GET /api/search

Search messages by query string. (FR-005, FR-006, FR-007)

**Requires**: Authentication

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| q | string | Yes | - | Search query (FTS5 syntax) |
| page | integer | No | 1 | Page number (1-indexed) |

**Response**: `200 OK`
```json
{
  "results": [
    {
      "id": 12345,
      "phone_number": "+15551234567",
      "contact_name": "John Doe",
      "body": "Message text with <mark>search</mark> term highlighted",
      "timestamp": 1234567890123,
      "message_type": 1,
      "formatted_date": "2024-01-15 10:30 AM"
    }
  ],
  "total": 523,
  "page": 1,
  "per_page": 50,
  "has_more": true
}
```

**Response Fields**:
- `results`: Array of matching messages
- `total`: Total number of matches
- `page`: Current page number
- `per_page`: Results per page (always 50)
- `has_more`: Boolean indicating more pages available
- `body`: HTML with `<mark>` tags around matched terms (FR-011 visual distinction)
- `message_type`: 1=received, 2=sent (FR-011)
- `formatted_date`: Human-readable date string

**Errors**:
- `400 Bad Request`: Missing `q` parameter
- `401 Unauthorized`: Not authenticated

### GET /api/stats

Get database statistics. (FR-008)

**Requires**: Authentication

**Response**: `200 OK`
```json
{
  "message_count": 247832,
  "has_messages": true
}
```

### GET /health

Health check endpoint for reverse proxy. (Constitution: Self-Hosting Requirements)

**Requires**: None (public)

**Response**: `200 OK`
```json
{
  "status": "ok"
}
```

---

## Error Responses

All API errors return JSON:

```json
{
  "error": "Error message description"
}
```

**HTTP Status Codes**:
- `400 Bad Request`: Invalid parameters
- `401 Unauthorized`: Authentication required
- `500 Internal Server Error`: Server error (no message content exposed per constitution)

---

## CLI: import.py

Not an HTTP API, but documented here for completeness.

### Usage

```bash
python import.py <path_to_backup.xml>
```

**Output** (to stdout):
```
Importing: backup.xml
Found 247,832 messages
Progress: 10,000 / 247,832 (4.0%)
Progress: 20,000 / 247,832 (8.1%)
...
Complete: 247,832 messages imported (12 duplicates skipped)
```

**Exit Codes**:
- `0`: Success
- `1`: File not found or invalid XML
- `2`: Database error

---

## Response Headers

All responses include:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy: default-src 'self'`

Session cookies include:
- `HttpOnly`
- `SameSite=Strict`
- `Secure` (when behind HTTPS proxy)
