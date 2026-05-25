# Soite Kotikuntoutus — Feedback System

## Live Demo
**Frontend:** [https://soite-feedback.vercel.app](https://soite-feedback.vercel.app)
**API:** [https://soite-feedback-backend.onrender.com/health](https://soite-feedback-backend.onrender.com/health)

Demo:https://soite-feedback-2tlgoy77i-aliipous-projects.vercel.app/

> A production-grade, anonymous patient feedback kiosk for **Soite's home rehabilitation team** (kotikuntoutus) in Kokkola, Finland.
>
> **Built by**: Ali Pourrahim — Centria University of Applied Sciences (Summer 2026)  
> **Stakeholders**: Anu Kamau (Centria), Minna LillKåla (Soite)

---

## Overview

Paper feedback forms produced 100+ responses/year. After migrating to a web form on soite.fi, responses dropped to 2/year. This PWA kiosk, deployed on HealthLab tablets at point of care, eliminates all friction: patients tap an answer on a large touch screen, and the data is sent anonymously and instantly.

**Key design principles:**
- **Anonymous by design** — zero PII collected; GDPR Article 9 risk eliminated at the source
- **Bilingual** — Finnish and Swedish; patient selects language at the start of each session
- **Offline-first** — submissions queue in IndexedDB and sync automatically on reconnect
- **Accessible** — WCAG 2.1 AA; large touch-friendly text; 4-face emoji scale for elderly tablet users
- **Secure** — JWT auth, bcrypt, rate limiting, pgcrypto encryption, HSTS, CSP

---

## Survey questions

The kiosk presents 5 face-scale questions followed by an optional free-text field. Patients first select their language (Finnish or Swedish). All questions editable via the admin panel.

| # | Finnish | Swedish | Type |
|---|---------|---------|------|
| 1 | Tunsitko, että sinua kuunneltiin ja sinua kohdeltiin kunnioittavasti? | Kände du att du blev lyssnad på och behandlad med respekt? | Face scale (1–4) |
| 2 | Saitko tarvitsemaasi apua ja ohjausta jakson aikana? | Fick du den hjälp och vägledning du behövde under perioden? | Face scale (1–4) |
| 3 | Koetko, että hoitoasi koskevat päätökset tehtiin yhteistyössä kanssasi? | Fattades besluten om din vård i samarbete med dig? | Face scale (1–4) |
| 4 | Koetko, että toimintakykysi on parantunut jakson myötä? | Upplever du att din funktionsförmåga har förbättrats under perioden? | Face scale (1–4) |
| 5 | Kuinka todennäköisesti suosittelisit palvelua vastaavassa tilanteessa olevalle? | Hur sannolikt är det att du skulle rekommendera tjänsten till någon i en liknande situation? | Face scale (1–4) |
| 6 | Vapaa sana ja kehitysideat | Fritt ord och utvecklingsidéer | Free text (optional) |

Face scale values: 1 = Erittäin tyytymätön / Mycket missnöjd · 2 = Tyytymätön / Missnöjd · 3 = Tyytyväinen / Nöjd · 4 = Erittäin tyytyväinen / Mycket nöjd

Questions are stored in the database and can be added, reordered, or deactivated at any time without a deploy.

---

## Quick start

```bash
# 1. Clone and configure
git clone https://github.com/aliipou/soite-feedback.git
cd soite-feedback
cp .env.example .env
# Edit .env — change SECRET_KEY and PGCRYPTO_KEY to unique random values

# 2. Start all services
docker compose up --build

# 3. Apply database migrations and seed default questions
docker compose exec backend alembic upgrade head

# 4. Create the first admin account
docker compose exec backend python -m app.cli create-admin \
  --email admin@soite.fi

# 5. Open the app
#   Kiosk (patient view): http://localhost:3000
#   Staff dashboard:      http://localhost:3000/dashboard
#   Admin panel:          http://localhost:3000/admin
#   API docs (dev only):  http://localhost:8000/docs
```

> **Generate secrets:**
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```
> Run this twice — once for `SECRET_KEY`, once for `PGCRYPTO_KEY`. They must be different.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend runtime | Python 3.12 |
| Web framework | FastAPI 0.111+ (async) |
| ORM | SQLAlchemy 2.x — async, mapped dataclasses |
| Database | PostgreSQL 16 |
| Migrations | Alembic |
| Validation | Pydantic v2 (`ConfigDict(strict=True)`) |
| Auth | PyJWT + passlib[bcrypt cost=12] |
| Rate limiting | slowapi + Redis (multi-worker safe) |
| HTML sanitisation | nh3 (Rust-backed; bleach is archived) |
| Logging | structlog (JSON in prod, console in dev) |
| Frontend | React 18 + TypeScript + Tailwind CSS 3 |
| Offline sync | Workbox PWA + IndexedDB (idb) |
| Container | Docker + Docker Compose v2 |
| CI | GitHub Actions |
| Linting | ruff + mypy (strict) |
| Testing | pytest + httpx (async) / Vitest + RTL |

---

## Repository layout

```
soite-feedback/
├── .env.example              ← copy to .env; never commit .env
├── .github/workflows/ci.yml  ← CI: lint, type-check, test, audit, docker build
├── docker-compose.yml        ← development (hot-reload, ports exposed)
├── docker-compose.prod.yml   ← production (gunicorn, health checks, restart policies)
├── nginx/
│   └── nginx.conf            ← HTTPS termination, rate-limit zone, security headers
├── docs/
│   ├── PRD.md                ← Product requirements and personas
│   ├── ARCHITECTURE.md       ← System design and ADRs
│   ├── API.md                ← REST API specification
│   ├── SECURITY.md           ← Threat model and OWASP mapping
│   ├── DATABASE.md           ← Schema, indexes, data dictionary
│   ├── GDPR.md               ← Legal basis, anonymisation, breach procedure
│   ├── DEVELOPMENT.md        ← Local setup, conventions, CI, deploy checklist
│   └── OPERATIONS.md         ← Production ops, backup, CSRF analysis
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml        ← dependencies, ruff config, mypy config
│   ├── alembic/
│   │   └── versions/
│   │       └── 0001_initial_schema.py   ← tables, indexes, triggers, seed data
│   ├── app/
│   │   ├── main.py           ← app factory, middleware, routers, lifespan
│   │   ├── config.py         ← Pydantic Settings with validation
│   │   ├── database.py       ← async engine, session factory, get_db dependency
│   │   ├── cli.py            ← create-admin, purge-old-data commands
│   │   ├── models/           ← SQLAlchemy mapped dataclasses
│   │   ├── schemas/          ← Pydantic v2 I/O models
│   │   ├── routers/          ← thin HTTP handlers (validate → service → return)
│   │   ├── services/         ← business logic (no HTTP, fully testable)
│   │   ├── security/         ← JWT, password hashing, FastAPI dependencies
│   │   └── middleware/       ← security headers, structured request logging
│   └── tests/
│       ├── conftest.py       ← SQLite in-memory fixtures, helpers
│       ├── security/         ← auth security, timing attacks, injection
│       ├── services/         ← feedback service, question service, user service
│       └── routers/          ← public, dashboard, admin endpoint tests
└── frontend/
    ├── Dockerfile            ← node build → nginx:alpine static serve
    ├── nginx.conf            ← SPA fallback, immutable cache headers
    ├── package.json
    └── src/
        ├── pages/            ← KioskPage, LoginPage, DashboardPage, AdminPage
        ├── components/
        │   ├── kiosk/        ← PrivacyNotice, Welcome, Question, ThankYou screens
        │   ├── dashboard/    ← charts, date range picker
        │   └── admin/        ← QuestionTable, UserTable, QuestionModal
        ├── hooks/            ← useAuth (silent refresh), useQuestions, useOnlineStatus
        ├── api/              ← typed API clients (axios)
        ├── auth/             ← ProtectedRoute, tokenStore (memory-only, not localStorage)
        ├── offline/          ← IndexedDB queue for offline submissions
        └── i18n/             ← react-i18next; Finnish (fi) + Swedish (sv)
```

---

## Development

### Running tests

```bash
# Backend tests (from repo root)
docker compose exec backend pytest -v

# With coverage report
docker compose exec backend pytest --cov=app --cov-report=term-missing

# Frontend tests
docker compose exec frontend npm test

# Or run outside Docker (requires local Python 3.12 + Node 20):
cd backend && pip install -e ".[dev]" && pytest
cd frontend && npm ci && npm test
```

Current test suite: **200+ tests** across services, routers, and security layers. Coverage ≥ 85% (`app/services/` and `app/routers/`). On SQLite (local), pgcrypto-dependent tests auto-skip; full suite runs on PostgreSQL in CI.

### Linting and type checking

```bash
# Backend
docker compose exec backend ruff check app/
docker compose exec backend mypy app/

# Frontend
docker compose exec frontend npm run type-check
docker compose exec frontend npm run lint
```

### Database migrations

```bash
# After changing a SQLAlchemy model:
docker compose exec backend alembic revision --autogenerate -m "describe_change"
docker compose exec backend alembic upgrade head

# Rollback one step
docker compose exec backend alembic downgrade -1
```

### Creating staff accounts

```bash
# Admin account (can manage questions and users)
docker compose exec backend python -m app.cli create-admin --email staff@soite.fi

# The CLI enforces password policy: min 12 chars, ≥1 uppercase, ≥1 digit
```

### Data retention

```bash
# Dry run — shows what would be deleted (older than 3 years)
docker compose exec backend python -m app.cli purge-old-data --dry-run

# Execute deletion (irreversible)
docker compose exec backend python -m app.cli purge-old-data
```

---

## Security

### Authentication model

- **Access token**: short-lived JWT (1h), stored in memory only — never in localStorage (XSS protection)
- **Refresh token**: 7-day, stored in `__Host-refresh_token` httpOnly cookie with `samesite=strict; path=/; secure`
- **Token rotation**: every refresh issues a new token and revokes the old one
- **Theft detection**: presenting a previously-revoked refresh token immediately revokes **all** sessions for that user
- **Silent re-auth**: on page reload, the frontend automatically attempts a silent refresh via the cookie, so users are not needlessly redirected to login

### Password security

- bcrypt with cost=12
- Minimum 12 characters, at least one uppercase letter, at least one digit
- Timing-safe comparison for both login and non-existent users (prevents user enumeration)

### Rate limiting

| Endpoint | Limit | Key |
|----------|-------|-----|
| `POST /feedback` | 3/hour | IP address |
| `POST /auth/login` | 5/15 min | IP address |

Redis-backed — safe with multiple Gunicorn workers.

### Security headers

Every response includes: `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy`, `Referrer-Policy`, `Permissions-Policy`, `X-Request-ID`.

### GDPR compliance

- No patient identifiers collected — anonymous by design
- Free-text answers encrypted at rest with `pgcrypto` (pgp_sym_encrypt)
- `device_token` identifies the tablet, not the patient; used only for rate limiting
- 3-year data retention enforced via CLI purge command
- See `docs/GDPR.md` for legal basis, DPA details, and breach procedure

---

## Production deployment

### Prerequisites

- A Linux server with Docker and Docker Compose v2 installed
- A domain name with DNS pointing to the server
- TLS certificate (Let's Encrypt recommended)

### Steps

```bash
# 1. Clone and configure production environment
cp .env.example .env
# Set ENVIRONMENT=production, ALLOWED_ORIGINS, strong SECRET_KEY and PGCRYPTO_KEY

# 2. Place TLS certificate
mkdir -p nginx/certs
# Copy fullchain.pem and privkey.pem to nginx/certs/

# 3. Build and start
docker compose -f docker-compose.prod.yml up -d --build

# 4. Run migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 5. Create admin user
docker compose -f docker-compose.prod.yml exec backend python -m app.cli create-admin \
  --email admin@soite.fi

# 6. Verify health
curl https://your-domain/api/v1/health
```

### Production checklist

- [ ] `ENVIRONMENT=production` in env
- [ ] `SECRET_KEY` ≥ 64 hex chars, not default
- [ ] `PGCRYPTO_KEY` ≥ 64 hex chars, different from `SECRET_KEY`
- [ ] `ALLOWED_ORIGINS` contains only the production domain
- [ ] `pip audit` passes (run in CI)
- [ ] `npm audit --audit-level=high` passes (run in CI)
- [ ] All migrations applied: `alembic upgrade head`
- [ ] Backup verified: `pg_dump` test restore
- [ ] HTTPS certificate valid and auto-renewing
- [ ] `GET /health` returns 200

---

## API overview

Base URL: `https://<host>/api/v1`

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /survey/questions` | None | Active questions in display order |
| `POST /feedback` | None (device token) | Submit anonymous feedback |
| `GET /health` | None | DB connectivity health check |
| `POST /auth/login` | — | Staff login → access token + refresh cookie |
| `POST /auth/refresh` | Cookie | Rotate refresh token |
| `POST /auth/logout` | Bearer | Revoke session |
| `GET /dashboard/summary` | Staff/Admin | Aggregate statistics |
| `GET /dashboard/freetext` | Staff/Admin | Paginated free-text answers |
| `GET /admin/questions` | Admin | All questions incl. inactive |
| `POST /admin/questions` | Admin | Create question |
| `PATCH /admin/questions/{id}` | Admin | Update question |
| `GET /admin/export` | Admin | Anonymised CSV export |
| `GET /admin/users` | Admin | List staff accounts |
| `POST /admin/users` | Admin | Create staff account |
| `PATCH /admin/users/{id}` | Admin | Deactivate or change role |

Full specification: [docs/API.md](./docs/API.md)

---

## Contributing

1. Fork and create a feature branch (`feat/<name>`)
2. Follow Conventional Commits: `feat:`, `fix:`, `security:`, `docs:`, `test:`, `chore:`
3. Run `ruff check`, `mypy`, and `pytest` — all must pass with ≥ 80% coverage on `services/` and `routers/`
4. Open a PR against `develop`; `main` is production-protected

---

## Documentation

| Document | Contents |
|----------|----------|
| [docs/PRD.md](./docs/PRD.md) | Product requirements, personas, milestones |
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | System design, ADRs, data flows |
| [docs/API.md](./docs/API.md) | Full REST API specification |
| [docs/SECURITY.md](./docs/SECURITY.md) | Threat model, OWASP mapping, mitigations |
| [docs/DATABASE.md](./docs/DATABASE.md) | Schema, data dictionary, retention policy |
| [docs/GDPR.md](./docs/GDPR.md) | Data protection, legal basis, breach procedure |
| [docs/DEVELOPMENT.md](./docs/DEVELOPMENT.md) | Local setup, conventions, CI, deploy checklist |
| [docs/OPERATIONS.md](./docs/OPERATIONS.md) | Production ops, backup, CSRF analysis |

---

## License

MIT — see LICENSE file. Note: this system handles healthcare-adjacent data; deploying organisations are responsible for their own GDPR compliance assessment.
