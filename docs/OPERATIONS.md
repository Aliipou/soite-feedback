# OPERATIONS.md — Production Operations

## 1. Docker production configuration

### docker-compose.prod.yml critical settings

```yaml
version: "3.9"

services:
  nginx:
    image: nginx:1.25-alpine@sha256:<digest>   # pin to digest, not tag
    restart: always
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/certs:/etc/nginx/certs:ro
      - frontend_build:/var/www/html:ro
    depends_on:
      backend:
        condition: service_healthy
    deploy:
      resources:
        limits:
          memory: 128m
          cpus: "0.5"

  backend:
    image: soite-feedback-backend:${APP_VERSION}
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    environment:
      - DATABASE_URL
      - REDIS_URL
      - SECRET_KEY
      - PGCRYPTO_KEY
      - ALLOWED_ORIGINS
      - ENVIRONMENT=production
      - APP_VERSION
    command: >
      gunicorn app.main:app
        -k uvicorn.workers.UvicornWorker
        --workers 3
        --bind 0.0.0.0:8000
        --timeout 30
        --graceful-timeout 10
        --keep-alive 5
        --log-level warning
        --access-logfile -
        --error-logfile -
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks: [soite_net]
    deploy:
      resources:
        limits:
          memory: 512m
          cpus: "1.0"

  db:
    image: postgres:16-alpine@sha256:<digest>
    restart: always
    environment:
      - POSTGRES_DB=soite_feedback
      - POSTGRES_USER=soite_app
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U soite_app -d soite_feedback"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks: [soite_net]
    deploy:
      resources:
        limits:
          memory: 512m
          cpus: "1.0"

  redis:
    image: redis:7-alpine@sha256:<digest>
    restart: always
    command: redis-server --maxmemory 64mb --maxmemory-policy allkeys-lru --requirepass ${REDIS_PASSWORD}
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
    networks: [soite_net]
    deploy:
      resources:
        limits:
          memory: 96m
          cpus: "0.25"

  backup:
    image: prodrigestivill/postgres-backup-local:16
    restart: always
    environment:
      - POSTGRES_HOST=db
      - POSTGRES_DB=soite_feedback
      - POSTGRES_USER=soite_app
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - SCHEDULE=@daily
      - BACKUP_KEEP_DAYS=30
      - BACKUP_KEEP_WEEKS=4
      - BACKUP_KEEP_MONTHS=3
    volumes:
      - ./backups:/backups
    depends_on:
      db:
        condition: service_healthy
    networks: [soite_net]

volumes:
  pg_data:
  frontend_build:

networks:
  soite_net:
    internal: true   # no direct internet access from containers
```

### Why gunicorn + uvicorn workers (not raw uvicorn)?
Raw `uvicorn --workers N` does not handle worker recycling on memory leaks or crashes. Gunicorn acts as a process manager: it restarts dead workers, gracefully drains in-flight requests before shutdown (`--graceful-timeout`), and handles SIGTERM correctly. This matters for zero-downtime deploys.

---

## 2. Dockerfile best practices

```dockerfile
# backend/Dockerfile

# Pin to digest for reproducible builds
FROM python:3.12-slim@sha256:<digest>

# Security: no .pyc files, unbuffered stdout for logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install deps first (layer cache) before copying source
COPY pyproject.toml poetry.lock ./
RUN pip install poetry==1.8.0 && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-root

COPY . .

# Security: run as non-root user
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup --no-create-home appuser && \
    chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

# Healthcheck at image level (also needed for docker-compose)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

`.dockerignore`:
```
.git
.gitignore
.env*
__pycache__
*.pyc
*.pyo
.pytest_cache
.mypy_cache
.ruff_cache
tests/
*.md
node_modules
```

---

## 3. Database connection pool

Configure SQLAlchemy engine explicitly — never rely on defaults:

```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,            # base connections kept alive
    max_overflow=10,        # additional connections under load
    pool_timeout=30,        # seconds to wait for a connection before raising
    pool_recycle=1800,      # recycle connections older than 30 min (prevents stale connections)
    pool_pre_ping=True,     # test connection before use (detects dropped connections)
    echo=settings.ENVIRONMENT == "development",
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
```

Without `pool_pre_ping=True`, after a PostgreSQL restart or idle timeout, the next request will get a `OperationalError: connection closed` error instead of transparently reconnecting.

Without `pool_recycle`, long-running servers accumulate stale TCP connections that fail silently.

---

## 4. Security: timing attack mitigations

### 4.1 Account enumeration via login timing
When a user logs in with an unknown email, bcrypt is NOT run (the user doesn't exist). This makes the response faster than for valid accounts, leaking whether an account exists.

Fix: always run bcrypt, even for non-existent users:

```python
# app/security/password.py
DUMMY_HASH = "$2b$12$notarealhashbutthesamelengthXXXXXXXXXXXXXXXXXXXXXXXXXX"

async def authenticate_user(db: AsyncSession, email: str, password: str):
    user = await get_user_by_email(db, email)
    if user is None:
        # Always run bcrypt to prevent timing-based account enumeration
        passlib_context.verify(password, DUMMY_HASH)
        return None
    if not passlib_context.verify(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user
```

### 4.2 Token comparison timing attack
Never compare tokens with `==`. Use `secrets.compare_digest()`:

```python
import secrets

# Bad
if stored_hash == computed_hash:
    ...

# Good
if secrets.compare_digest(stored_hash.encode(), computed_hash.encode()):
    ...
```

### 4.3 JWT algorithm confusion attack
Always explicitly specify allowed algorithms when decoding:

```python
import jwt

# Bad — allows attacker to switch to 'none' algorithm
payload = jwt.decode(token, secret, algorithms=jwt.algorithms.get_default_algorithms())

# Good
payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
```

### 4.4 Refresh token theft detection
If a refresh token that has already been rotated (revoked) is presented, it indicates the original refresh token was stolen and used by an attacker. Response: revoke ALL active refresh tokens for that user.

```python
async def rotate_refresh_token(db: AsyncSession, token: str):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    stored = await get_refresh_token_by_hash(db, token_hash)

    if stored is None:
        raise HTTPException(401, "Invalid refresh token")

    if stored.revoked_at is not None:
        # Token was already rotated — potential theft detected
        # Revoke ALL tokens for this user immediately
        await revoke_all_user_tokens(db, stored.user_id)
        raise HTTPException(401, "Session invalidated. Please log in again.")

    if stored.expires_at < datetime.utcnow():
        raise HTTPException(401, "Refresh token expired")

    # Revoke old token, issue new one
    await revoke_token(db, stored.id)
    new_token = await create_refresh_token(db, stored.user_id)
    return new_token
```

### 4.5 Cookie prefix `__Host-`
The `__Host-` prefix prevents subdomain attacks — the browser will only send the cookie to the exact domain that set it, not subdomains:

```python
response.set_cookie(
    key="__Host-refresh_token",   # ← prefix prevents subdomain attacks
    value=token,
    httponly=True,
    secure=True,         # required for __Host- prefix
    samesite="strict",
    path="/",            # required for __Host- prefix (must be /)
    max_age=604800,
)
```

Note: `__Host-` requires `path="/"` and `secure=True` and no `domain` attribute. Cannot scope to `/auth/refresh` with this prefix — trade-off documented.

---

## 5. CSRF analysis: public endpoint

**The `/api/v1/feedback` public endpoint does NOT need CSRF protection.**

Reason: CSRF attacks work by tricking a victim's browser into making an authenticated request. This endpoint:
1. Has no authentication
2. Only accepts `Content-Type: application/json`
3. Is protected by CORS

A cross-origin form POST with `application/json` is blocked by browsers (CORS preflight fails). A cross-origin attacker cannot set `Content-Type: application/json` without triggering CORS preflight, which the CORS policy blocks.

CSRF protection adds a round-trip (GET /csrf → POST /feedback) with no security benefit on this endpoint. **Remove it from the public kiosk flow.**

Retain CSRF protection only on authenticated state-changing endpoints (admin write operations).

---

## 6. React PWA: error boundary and update strategy

### Error boundary (prevents blank screen on JS crash)
```tsx
// src/components/ErrorBoundary.tsx
import { Component, ReactNode } from "react";

interface Props { children: ReactNode }
interface State { hasError: boolean }

export class ErrorBoundary extends Component<Props, State> {
    state: State = { hasError: false };

    static getDerivedStateFromError() {
        return { hasError: true };
    }

    componentDidCatch(error: Error) {
        // Log to structured error tracking (not console.log — no PII)
        console.error("Unhandled error:", error.message);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div style={{ textAlign: "center", padding: "2rem" }}>
                    <h1>Jokin meni pieleen</h1>
                    <p>Pyydä hoitajaa käynnistämään laite uudelleen.</p>
                </div>
            );
        }
        return this.props.children;
    }
}
```

### Service worker update strategy
When questions change, the cached service worker serves stale questions until the PWA is updated. Strategy:

```ts
// src/serviceWorkerRegistration.ts
navigator.serviceWorker.register('/sw.js').then(reg => {
    reg.addEventListener('updatefound', () => {
        const newWorker = reg.installing!;
        newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // New version available — force immediate activation
                // (kiosk: no user prompt needed, just reload)
                newWorker.postMessage({ type: 'SKIP_WAITING' });
                window.location.reload();
            }
        });
    });
});
```

The kiosk should reload automatically when a new version is deployed — no user action needed.

---

## 7. SSL certificate automation

```bash
# Install certbot on the host
apt-get install certbot

# Obtain certificate (standalone mode, stop nginx first)
certbot certonly --standalone -d yourdomain.fi

# Auto-renewal cron (runs twice daily)
echo "0 0,12 * * * root certbot renew --quiet --deploy-hook 'docker compose -f /path/to/docker-compose.prod.yml restart nginx'" | tee /etc/cron.d/certbot-renew

# Verify auto-renewal works
certbot renew --dry-run
```

---

## 8. Backup verification procedure

A backup that has never been tested is not a backup.

```bash
# Monthly restore test procedure (run on a separate machine)
# 1. Get latest backup
ls -lt backups/ | head -5

# 2. Restore to a test container
docker run -d --name pg-restore-test \
  -e POSTGRES_DB=soite_test \
  -e POSTGRES_USER=soite_app \
  -e POSTGRES_PASSWORD=testpass \
  postgres:16-alpine

# 3. Restore
gunzip -c backups/latest.sql.gz | \
  docker exec -i pg-restore-test psql -U soite_app soite_test

# 4. Verify row counts match production
docker exec pg-restore-test psql -U soite_app soite_test \
  -c "SELECT COUNT(*) FROM feedback_submissions;"

# 5. Cleanup
docker rm -f pg-restore-test
```

Document the result in a `docs/backup-log.md` file with date and row counts.

---

## 9. Graceful shutdown

FastAPI/uvicorn handles SIGTERM but background tasks (e.g., purge jobs) need to be cancelled cleanly:

```python
# app/main.py
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await startup_checks()
    yield
    # Shutdown — cancel any running background tasks
    tasks = [t for t in asyncio.all_tasks() if t.get_name().startswith("background_")]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

app = FastAPI(lifespan=lifespan)
```

---

## 10. Metrics (minimal Prometheus)

```python
# app/middleware/metrics.py
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
import time

REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests",
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", "HTTP request latency",
    ["endpoint"]
)
FEEDBACK_COUNT = Counter(
    "feedback_submissions_total", "Total feedback submissions"
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    latency = time.time() - start
    REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
    REQUEST_LATENCY.labels(request.url.path).observe(latency)
    return response

@app.get("/metrics")
async def metrics():
    # Restrict to internal network only (Nginx blocks external access)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

Add to nginx.conf: deny external access to `/metrics`.
