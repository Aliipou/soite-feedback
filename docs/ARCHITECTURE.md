# ARCHITECTURE.md — System Design

## 1. High-level overview

```
┌─────────────────────────────────────────────────────────┐
│                     HealthLab Tablet                    │
│              React PWA (offline-capable)                │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTPS + JWT
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Application                    │
│  Rate limiter → Auth guard → Router → Service layer     │
└───────────────────────┬─────────────────────────────────┘
                        │ SQLAlchemy async
                        ▼
┌─────────────────────────────────────────────────────────┐
│             PostgreSQL 16 (Docker volume)               │
│          Encrypted at rest · Daily backup               │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Architecture Decision Records (ADRs)

### ADR-001: FastAPI over Django
**Status**: Accepted  
**Context**: Need async I/O for offline PWA sync bursts; OpenAPI docs generated automatically; team has FastAPI experience.  
**Decision**: FastAPI with async SQLAlchemy.  
**Consequences**: Need to manage migrations manually via Alembic; no built-in admin panel (we build our own).

### ADR-002: PostgreSQL over SQLite
**Status**: Accepted  
**Context**: Multi-tablet concurrent writes; production-grade ACID guarantees needed; JSON column for flexible question schema.  
**Decision**: PostgreSQL 16 in Docker.  
**Consequences**: Slightly heavier local dev setup; mitigated by Docker Compose one-command start.

### ADR-003: PWA over native app
**Status**: Accepted  
**Context**: HealthLab tablets run Android Chrome; Centria students cannot publish to Play Store; offline capability is needed.  
**Decision**: React PWA with service worker caching survey questions.  
**Consequences**: No push notifications (acceptable for v1); offline submission queue stored in IndexedDB, synced on reconnect.

### ADR-004: Anonymous submissions — no session linking
**Status**: Accepted  
**Context**: GDPR Article 9 — health-related feedback from identifiable patients is special-category data. Anonymising at collection eliminates the legal obligation entirely.  
**Decision**: Each tablet generates a random `device_token` (UUID v4) on first boot, stored in localStorage. This token identifies the *device*, not the patient. It is used only for rate limiting.  
**Consequences**: Cannot deduplicate responses from the same patient across visits; acceptable because the goal is aggregate statistics, not individual tracking.

### ADR-005: JWT over session cookies for staff
**Status**: Accepted  
**Context**: Staff access dashboard from various browsers; stateless auth reduces server complexity.  
**Decision**: Short-lived access token (1 hour) + refresh token (7 days, httpOnly cookie).  
**Consequences**: Must implement token rotation on refresh; revocation list needed for logout (Redis or DB table).

### ADR-006: Docker Compose for all environments
**Status**: Accepted  
**Context**: Reproducible dev/staging/prod; easy handover to Soite/HealthLab.  
**Decision**: `docker-compose.yml` for dev (with hot reload), `docker-compose.prod.yml` for production (no volume mounts, health checks, restart policies).  
**Consequences**: Requires Docker on deployment server; Soite IT must confirm this is available.

---

## 3. Data flow — feedback submission

```
Patient taps emoji answer
        │
        ▼
React stores answer in component state
        │
Patient taps "Seuraava" (Next)
        │
After final question → confirmation screen
        │
        ▼
POST /api/v1/feedback
  Headers: X-Device-Token, Content-Type: application/json
  Body: { answers: [{question_id, value, text?}], submitted_at_local }
        │
        ▼
Rate limiter checks: device_token → max 3/hour
        │
        ▼
Pydantic validates: all question_ids exist and are active; values in range
        │
        ▼
Service layer: create FeedbackSubmission + FeedbackAnswer rows (ORM)
        │
        ▼
200 OK → { submission_id (opaque UUID) }
        │
        ▼
Frontend shows "Kiitos palautteestasi!" → 10-second countdown → reset
```

---

## 4. Data flow — offline mode

```
Tablet loses network
        │
        ▼
Service worker intercepts POST /api/v1/feedback
        │
        ▼
Stores serialised payload in IndexedDB queue
        │
        ▼
Shows confirmation screen (patient doesn't notice)
        │
Network restored
        │
        ▼
Background sync (workbox) drains IndexedDB queue
        │
        ▼
Deduplication: submission_id (UUID generated client-side) prevents double-writes
```

---

## 5. Deployment topology

```
[Nginx reverse proxy]  ← HTTPS termination, HSTS, gzip
        │
   [FastAPI container]  ← uvicorn workers (2× CPU count)
        │
   [PostgreSQL container]  ← named Docker volume
        │
   [pgBackup sidecar]  ← daily pg_dump to S3 or local volume
```

All containers in a single `docker-compose.prod.yml` network (`soite_net`, internal).  
Nginx is the only container with exposed ports (80 → redirect 443, 443).
