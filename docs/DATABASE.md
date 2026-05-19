# DATABASE.md — Schema & Data Dictionary

## 1. Design principles

- **No PII ever** — no patient name, DOB, contact info, room number
- **Device token ≠ identity** — `device_token` identifies hardware for rate limiting only
- **Free-text encrypted** — `pgcrypto` symmetric encryption for optional text answers
- **Soft deletes** — questions are never hard-deleted; `is_active = false` instead
- **Audit log is append-only** — no UPDATE or DELETE on `audit_log`

---

## 2. Tables

### `questions`
Stores the survey questions managed by admin.

```sql
CREATE TABLE questions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text_fi       TEXT        NOT NULL,           -- Finnish (required)
    text_en       TEXT,                           -- English (optional)
    question_type VARCHAR(16) NOT NULL            -- 'scale5' | 'yesno' | 'text'
                  CHECK (question_type IN ('scale5', 'yesno', 'text')),
    display_order SMALLINT    NOT NULL DEFAULT 0,
    is_active     BOOLEAN     NOT NULL DEFAULT true,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_questions_active_order ON questions (is_active, display_order);
```

### `feedback_submissions`
One row per completed survey. Contains no patient data.

```sql
CREATE TABLE feedback_submissions (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_submission_id UUID        NOT NULL UNIQUE,  -- client-generated; used for idempotency
    device_token         UUID        NOT NULL,          -- identifies tablet, not patient
    submitted_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    question_count       SMALLINT    NOT NULL,
    app_version          VARCHAR(16)
);

CREATE INDEX idx_submissions_submitted_at ON feedback_submissions (submitted_at DESC);
CREATE INDEX idx_submissions_device       ON feedback_submissions (device_token);
```

### `feedback_answers`
Individual answers within a submission.

```sql
CREATE TABLE feedback_answers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id   UUID        NOT NULL REFERENCES feedback_submissions(id) ON DELETE CASCADE,
    question_id     UUID        NOT NULL REFERENCES questions(id) ON DELETE RESTRICT,
    int_value       SMALLINT    CHECK (int_value IS NULL OR int_value BETWEEN 0 AND 5),
    text_value      BYTEA,                         -- pgcrypto pgp_sym_encrypt() output
    answered_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_submission_question UNIQUE (submission_id, question_id)
);

CREATE INDEX idx_answers_submission ON feedback_answers (submission_id);
CREATE INDEX idx_answers_question   ON feedback_answers (question_id);
```

### `staff_users`
Staff and admin accounts. No patient data here.

```sql
CREATE TABLE staff_users (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email                 VARCHAR(254) NOT NULL UNIQUE,
    hashed_password       TEXT         NOT NULL,  -- TEXT not VARCHAR(60): future-proof for argon2
    role                  VARCHAR(16)  NOT NULL DEFAULT 'staff'
                          CHECK (role IN ('staff', 'admin')),
    is_active             BOOLEAN      NOT NULL DEFAULT true,
    force_password_change BOOLEAN      NOT NULL DEFAULT true,  -- true on account creation
    last_login_at         TIMESTAMPTZ,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT now()
);
```

### `refresh_tokens`
Tracks issued refresh tokens for rotation and revocation.

```sql
CREATE TABLE refresh_tokens (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES staff_users(id) ON DELETE CASCADE,
    token_hash      VARCHAR(64) NOT NULL UNIQUE,   -- SHA-256 of the actual token
    expires_at      TIMESTAMPTZ NOT NULL,
    revoked_at      TIMESTAMPTZ,                   -- NULL = still valid
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_refresh_token_hash   ON refresh_tokens (token_hash);
CREATE INDEX idx_refresh_user_active  ON refresh_tokens (user_id) WHERE revoked_at IS NULL;
CREATE INDEX idx_refresh_expires      ON refresh_tokens (expires_at) WHERE revoked_at IS NULL;
```

### `audit_log`
Append-only. Records every admin action.

```sql
CREATE TABLE audit_log (
    id          BIGSERIAL   PRIMARY KEY,
    actor_id    UUID        REFERENCES staff_users(id),
    action      VARCHAR(64) NOT NULL,              -- e.g. 'question.create', 'question.deactivate'
    target_id   UUID,                              -- ID of affected row
    before_json JSONB,                             -- state before change (null for creates)
    after_json  JSONB,                             -- state after change (null for deletes)
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Audit log is append-only: revoke UPDATE and DELETE from application role
REVOKE UPDATE, DELETE ON audit_log FROM soite_app;
```

---

## 3. Required PostgreSQL extensions

```sql
-- Must be in the first Alembic migration (0001_initial_schema.py)
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

## 4. Triggers

```sql
-- Auto-update updated_at on questions table
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_questions_updated_at
BEFORE UPDATE ON questions
FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

## 5. Free-text encryption

Use `pgp_sym_encrypt` / `pgp_sym_decrypt` from pgcrypto. The key comes from `PGCRYPTO_KEY` env var, passed as a bind parameter — never hardcoded.

```sql
-- Write (in SQLAlchemy via text())
INSERT INTO feedback_answers (submission_id, question_id, text_value)
VALUES (:sid, :qid, pgp_sym_encrypt(:plaintext, :key));

-- Read
SELECT pgp_sym_decrypt(text_value, :key) FROM feedback_answers WHERE ...;
```

⚠️ `PGCRYPTO_KEY` must be different from `SECRET_KEY`. Both are in `.env`, never committed.

## 6. Database roles

```sql
-- Application role (used by FastAPI)
CREATE ROLE soite_app LOGIN PASSWORD '...';
GRANT SELECT, INSERT, UPDATE, DELETE ON feedback_submissions, feedback_answers, questions, staff_users, refresh_tokens TO soite_app;
GRANT INSERT ON audit_log TO soite_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO soite_app;

-- Read-only role (used by backup and reporting)
CREATE ROLE soite_readonly LOGIN PASSWORD '...';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO soite_readonly;
```

---

## 4. Migration strategy (Alembic)

```
alembic/
├── env.py
├── script.py.mako
└── versions/
    ├── 0001_initial_schema.py
    ├── 0002_add_app_version_to_submissions.py
    └── ...
```

Rules:
- Never edit a committed migration; always create a new one
- Every migration must have a `downgrade()` function
- Migrations run automatically on container startup in development; manually reviewed in production

---

## 5. Data retention

- `feedback_submissions` + `feedback_answers`: retained 3 years, then purged by scheduled job
- `audit_log`: retained 5 years (legal requirement for public sector)
- `staff_users`: deactivated users retained 1 year after deactivation, then anonymised (email → `deleted_{id}@deleted`)
- Backup files: 30-day retention on backup storage
