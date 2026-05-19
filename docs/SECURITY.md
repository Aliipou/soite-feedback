# SECURITY.md — Threat Model & Mitigations

## 1. Asset inventory

| Asset | Sensitivity | Location |
|-------|-------------|----------|
| Feedback responses (aggregate) | Low — anonymous | PostgreSQL |
| Free-text responses | Medium — may contain incidental PII | PostgreSQL, encrypted column |
| Staff credentials (bcrypt hash) | High | PostgreSQL |
| JWT secret key | Critical | Environment variable only |
| Question content | Low | PostgreSQL |
| Audit log | Medium | PostgreSQL |

---

## 2. Threat model (STRIDE)

### 2.1 Spoofing
| Threat | Mitigation |
|--------|------------|
| Attacker submits feedback as another device | Device token is rate-limit only, not identity — no spoofing value |
| Staff token stolen and reused | Access tokens expire in 1 hour; refresh tokens are rotated on each use and stored httpOnly |
| Admin credential brute force | bcrypt (cost=12) + 5 attempts/15min rate limit + account lockout after 10 failures |

### 2.2 Tampering
| Threat | Mitigation |
|--------|------------|
| Modify question IDs in submission payload | Server validates all `question_id` values exist and are active in DB |
| Inject SQL via input fields | SQLAlchemy ORM exclusively — no string interpolation in queries |
| Modify JWT payload | HS256 signature with 32-byte secret; validated on every request |
| Man-in-the-middle | HSTS with 1-year max-age; preload list submission recommended |

### 2.3 Repudiation
| Threat | Mitigation |
|--------|------------|
| Admin denies making a change | Immutable audit log: every write to `questions` table logged with actor, timestamp, before/after JSON |
| Staff denies viewing data | Access log at Nginx level + application-level audit for data exports |

### 2.4 Information disclosure
| Threat | Mitigation |
|--------|------------|
| Database dump exposes PII | No PII collected — anonymised at ingestion |
| Free-text contains accidental PII | Column encrypted with `pgcrypto`; only decrypted server-side for authorised staff |
| Error messages leak stack traces | `ENVIRONMENT=production` → generic 500 response; full trace to stderr/log only |
| Log files contain patient data | Logging policy: log only method, path, status, latency — never request body |
| API reveals internal structure | No stack traces in responses; no `X-Powered-By` header |

### 2.5 Denial of service
| Threat | Mitigation |
|--------|------------|
| Flood submission endpoint | 3 submissions/hour per device token (slowapi) |
| Flood auth endpoint | 5 attempts/15min per IP (slowapi) |
| Large payload upload | Max request body 50 KB (FastAPI `limit_concurrency` + Nginx `client_max_body_size 50k`) |
| Slow-loris | Nginx handles connection management; uvicorn behind proxy |

### 2.6 Elevation of privilege
| Threat | Mitigation |
|--------|------------|
| Staff role accesses admin endpoints | JWT `role` claim checked on every admin route via FastAPI dependency |
| Anonymous user accesses staff dashboard | All dashboard routes require valid JWT; 401 on missing/invalid token |
| Container escapes to host | Docker containers run as non-root (`USER appuser`); read-only root filesystem where possible |

---

## 3. OWASP Top 10 mapping

| OWASP | Risk | Our mitigation |
|-------|------|----------------|
| A01 Broken Access Control | High | Role-based JWT deps on every protected route; anonymous routes explicitly listed |
| A02 Cryptographic Failures | High | bcrypt(12) for passwords; pgcrypto for free-text; TLS 1.2+ enforced |
| A03 Injection | High | SQLAlchemy ORM; Pydantic strict validation; nh3 for HTML sanitisation |
| A04 Insecure Design | Medium | ADR-004 (anonymous by design); threat model documented and reviewed |
| A05 Security Misconfiguration | High | Hardened Dockerfile; no debug in prod; dependency audit in CI |
| A06 Vulnerable Components | Medium | `pip audit` + `npm audit` in CI; Dependabot alerts |
| A07 Auth Failures | High | Short-lived tokens; refresh rotation; bcrypt; rate limits |
| A08 Software Integrity | Medium | Pinned Docker base images; lockfiles committed (poetry.lock, package-lock.json) |
| A09 Logging Failures | Medium | Structured logging (structlog); audit trail for all writes; no body logging |
| A10 SSRF | Low | No user-controlled URL fetching in v1 |

---

## 4. Security headers (enforced by middleware)

```python
# app/middleware/security_headers.py
SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "  # Tailwind requires this
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    ),
}
```

---

## 5. Input validation rules

| Field | Type | Max length | Allowed values |
|-------|------|-----------|----------------|
| `question_id` | UUID | — | Must exist in DB |
| `value` (emoji scale) | int | — | 1–5 inclusive |
| `value` (yes/no) | bool | — | true/false |
| `text` (free text) | str, optional | 500 chars | nh3.clean()-stripped; no HTML |
| `submitted_at_local` | ISO 8601 datetime | — | Accepted but not trusted; server timestamp used |

---

## 6. Dependency audit procedure

```bash
# Backend — run before every release
pip audit

# Frontend
npm audit --audit-level=high

# Docker base image — check for known CVEs
docker scout cves soite-feedback-backend:latest
```

CI pipeline blocks merge if any HIGH or CRITICAL severity CVE is found.

---

## 7. Incident response checklist

If a security issue is suspected:
1. Immediately rotate `SECRET_KEY` and invalidate all active tokens
2. Review audit log for anomalous access patterns
3. If data exposure suspected: notify Soite DPO within 72 hours (GDPR Article 33)
4. Patch and redeploy; tag release as `security:` commit
5. Post-mortem document within 5 business days
