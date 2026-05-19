# API.md — REST API Specification

Base URL: `https://<host>/api/v1`  
All requests/responses: `Content-Type: application/json`  
All timestamps: ISO 8601 with timezone (`2026-05-17T14:30:00+03:00`)

---

## Authentication

### `POST /auth/login`
Staff login. No rate limit bypass — 5 attempts/15min per IP.

**Request**
```json
{
  "email": "staff@soite.fi",
  "password": "..."
}
```

**Response 200**
```json
{
  "access_token": "<JWT>",
  "token_type": "bearer",
  "expires_in": 3600
}
```
Sets `refresh_token` httpOnly cookie (7 days).

**Errors**
- `401` — invalid credentials (generic message, no account enumeration)
- `429` — rate limit exceeded

---

### `POST /auth/refresh`
Rotate refresh token. Requires valid `refresh_token` cookie.

**Response 200** — same as login  
**Errors**: `401` if token expired/revoked

---

### `POST /auth/logout`
Revokes current refresh token.

**Headers**: `Authorization: Bearer <access_token>`  
**Response 204** — no body

---

## Public endpoints (no auth)

### `GET /survey/questions`
Returns active questions in display order. Cached 5 minutes server-side.

**Response 200**
```json
{
  "questions": [
    {
      "id": "3fa85f64-...",
      "text_fi": "Kuinka tyytyväinen olit saamaasi palveluun?",
      "text_en": "How satisfied were you with the service received?",
      "type": "scale5",
      "order": 1
    },
    {
      "id": "9bd12c44-...",
      "text_fi": "Saitko riittävästi tietoa kuntoutuksestasi?",
      "text_en": "Did you receive enough information about your rehabilitation?",
      "type": "yesno",
      "order": 2
    },
    {
      "id": "a1b2c3d4-...",
      "text_fi": "Haluatko antaa muuta palautetta?",
      "text_en": "Would you like to give any other feedback?",
      "type": "text",
      "order": 3
    }
  ],
  "version": "2026-05-17T09:00:00Z"
}
```

---

### `POST /feedback`
Submit a completed survey. Rate limited: 3 per hour per IP.

No CSRF token required — JSON-only API protected by CORS preflight. See OPERATIONS.md §5.

**Headers**
```
X-Device-Token: <UUID v4>
Content-Type: application/json
```

**Request**
```json
{
  "submission_id": "<UUID v4 generated client-side>",
  "answers": [
    { "question_id": "3fa85f64-...", "int_value": 4 },
    { "question_id": "9bd12c44-...", "int_value": 1 },
    { "question_id": "a1b2c3d4-...", "text_value": "Hoitajat olivat mukavia." }
  ],
  "submitted_at_local": "2026-05-17T14:28:00+03:00",
  "app_version": "1.0.0"
}
```

**Validation rules**
- All active `question_id`s must be answered (no skipping non-text questions)
- `int_value` for `scale5`: 1–5
- `int_value` for `yesno`: 0 or 1
- `text_value`: max 500 characters, stripped of HTML
- `submission_id`: UUID v4 format; duplicate submissions (same ID) return 200 idempotently

**Response 200**
```json
{ "received": true }
```

**Errors**
- `400` — validation failure with field-level detail
- `409` — already submitted (idempotency key collision, safe to retry)
- `429` — rate limit exceeded
- `422` — invalid question IDs

---

## Staff endpoints (JWT required, role: staff or admin)

### `GET /dashboard/summary`
Aggregate statistics.

**Query params**: `from` (ISO date), `to` (ISO date). Default: last 30 days.

**Response 200**
```json
{
  "period": { "from": "2026-04-17", "to": "2026-05-17" },
  "total_submissions": 47,
  "by_question": [
    {
      "question_id": "3fa85f64-...",
      "text_fi": "Kuinka tyytyväinen...",
      "type": "scale5",
      "counts": { "1": 0, "2": 1, "3": 4, "4": 18, "5": 24 },
      "mean": 4.38
    }
  ]
}
```

---

### `GET /dashboard/freetext`
Free-text answers, paginated. No metadata (no timestamps, no device info).

**Query params**: `question_id` (required), `page` (default 1), `per_page` (default 20, max 50)

**Response 200**
```json
{
  "total": 12,
  "page": 1,
  "items": [
    { "text": "Hoitajat olivat mukavia ja ammattitaitoisia." },
    { "text": "Toivoisin useampia käyntejä viikossa." }
  ]
}
```

---

## Admin endpoints (JWT required, role: admin)

### `GET /admin/questions`
All questions including inactive.

### `POST /admin/questions`
Create a new question.

**Request**
```json
{
  "text_fi": "Suosittelisitko palveluamme muille?",
  "text_en": "Would you recommend our service to others?",
  "type": "yesno",
  "order": 4
}
```

### `PATCH /admin/questions/{id}`
Update question text, order, or active status. Logs to `audit_log`.

### `GET /admin/export`
Returns anonymised CSV of all responses in date range.

**Query params**: `from`, `to`  
**Response**: `Content-Type: text/csv; charset=utf-8`

### `GET /admin/users`
List staff accounts.

### `POST /admin/users`
Create staff account.

### `PATCH /admin/users/{id}`
Deactivate or change role.

---

## Error response format

All errors follow this structure:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "fields": {
      "answers[0].int_value": "Must be between 1 and 5"
    }
  }
}
```

Standard codes: `VALIDATION_ERROR`, `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `RATE_LIMITED`, `INTERNAL_ERROR`
