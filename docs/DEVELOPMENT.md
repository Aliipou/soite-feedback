# DEVELOPMENT.md — Local Setup & Conventions

## 1. Prerequisites

- Docker Desktop ≥ 4.x
- Python 3.12 (for running tools outside container)
- Node.js 20 LTS (for frontend outside container)
- `make` (optional but recommended)

---

## 2. First-time setup

```bash
git clone https://github.com/<org>/soite-feedback.git
cd soite-feedback

# Copy env template
cp .env.example .env
# Edit .env — change SECRET_KEY at minimum

# Start all services
docker compose up --build

# Run migrations
docker compose exec backend alembic upgrade head

# Create first admin user
docker compose exec backend python -m app.cli create-admin --email admin@soite.fi

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API docs: http://localhost:8000/docs
```

---

## 3. Daily development workflow

```bash
# Start services (hot reload enabled for both frontend and backend)
docker compose up

# Run backend tests
docker compose exec backend pytest -v

# Run with coverage
docker compose exec backend pytest --cov=app --cov-report=term-missing

# Type check
docker compose exec backend mypy app/

# Lint
docker compose exec backend ruff check app/

# Frontend tests
docker compose exec frontend npm test

# Create a new migration after model changes
docker compose exec backend alembic revision --autogenerate -m "add_xyz_column"
docker compose exec backend alembic upgrade head
```

---

## 4. Project conventions

### 4.1 Branch strategy
```
main          ← production-ready; protected; requires PR + review
develop       ← integration branch
feat/<name>   ← feature branches
fix/<name>    ← bug fixes
security/<name> ← security patches (may bypass normal review for critical issues)
```

### 4.2 Commit messages (Conventional Commits)
```
feat: add CSV export endpoint
fix: correct CSRF token validation on mobile Safari
security: rotate JWT signing algorithm to RS256
docs: update API.md with new export endpoint
test: add edge cases for rate limiter
chore: upgrade FastAPI to 0.112.0
```

### 4.3 Backend structure
```
app/
├── main.py          ← FastAPI app creation, middleware registration, router inclusion
├── config.py        ← Pydantic Settings (reads from .env)
├── database.py      ← async engine, session factory, get_db dependency
├── models/          ← SQLAlchemy mapped dataclasses
│   ├── question.py
│   ├── feedback.py
│   └── user.py
├── schemas/         ← Pydantic v2 models (request/response)
│   ├── feedback.py
│   ├── question.py
│   └── user.py
├── routers/         ← FastAPI routers (thin: validate → call service → return)
│   ├── public.py    ← /survey, /feedback
│   ├── auth.py      ← /auth
│   ├── dashboard.py ← /dashboard
│   └── admin.py     ← /admin
├── services/        ← Business logic (no HTTP, no DB sessions — testable in isolation)
│   ├── feedback.py
│   ├── question.py
│   └── user.py
├── security/        ← JWT, password hashing, FastAPI dependencies
│   ├── jwt.py
│   ├── password.py
│   └── dependencies.py
├── middleware/      ← Security headers, request logging
└── cli.py           ← Management commands (create-admin, purge-old-data)
```

### 4.4 Naming conventions
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Database columns: `snake_case`
- API routes: `kebab-case` (`/admin/staff-users`)

---

## 5. Testing conventions

```python
# tests/test_feedback_service.py

import pytest
from app.services.feedback import create_submission
from tests.factories import QuestionFactory, SubmissionFactory

@pytest.mark.asyncio
async def test_submission_happy_path(db_session, active_questions):
    """Submission with valid answers for all active questions succeeds."""
    ...

@pytest.mark.asyncio
async def test_submission_invalid_scale_value(db_session, active_questions):
    """Scale answer outside 1-5 raises ValidationError."""
    ...

@pytest.mark.asyncio
async def test_submission_idempotent(db_session, active_questions):
    """Submitting same submission_id twice returns success without duplicate row."""
    ...
```

Coverage target: 80% on `services/` and `routers/`.

---

## 6. CI pipeline (GitHub Actions)

```yaml
# .github/workflows/ci.yml
on: [push, pull_request]
jobs:
  backend:
    steps:
      - ruff check
      - mypy app/ --strict
      - pytest --cov=app --cov-fail-under=80
      - pip audit          # blocks on HIGH/CRITICAL CVEs
  frontend:
    steps:
      - npm run type-check
      - npm test
      - npm audit --audit-level=high
  docker:
    steps:
      - docker build (both images)
      - docker scout cves (informational, does not block)
```

---

## 7. Production deployment checklist

Before each production deploy:

- [ ] `ENVIRONMENT=production` in env
- [ ] `DEBUG=false`
- [ ] `SECRET_KEY` is 32+ random bytes, not the dev default
- [ ] `ALLOWED_ORIGINS` contains only the production domain
- [ ] `pip audit` passes
- [ ] `npm audit --audit-level=high` passes
- [ ] All migrations applied: `alembic upgrade head`
- [ ] Backup verified: `pg_dump` test restore
- [ ] HTTPS certificate valid and auto-renewing (Let's Encrypt / certbot)
- [ ] Health check endpoint returns 200: `GET /health`
