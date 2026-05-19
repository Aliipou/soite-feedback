# TESTING.md — Test Strategy

## 1. Test pyramid

```
        ┌──────────┐
        │    E2E   │  ← Playwright: 3–5 critical flows only
        ├──────────┤
        │ Integr.  │  ← pytest + real DB (testcontainers): 20–30 tests
        ├──────────┤
        │   Unit   │  ← pytest: 80+ tests, services only, no I/O
        └──────────┘
```

Coverage target: **≥ 80%** on `app/services/`, `app/routers/`, `app/security/`

---

## 2. Unit tests — service layer

### Test structure conventions
```python
# tests/services/test_feedback_service.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.feedback import create_submission, FeedbackValidationError

class TestCreateSubmission:
    """All tests for create_submission service function."""

    async def test_happy_path(self, db_session, active_questions):
        """Valid answers for all active questions → submission created."""
        ...

    async def test_duplicate_submission_id_is_idempotent(self, db_session, active_questions):
        """Same client_submission_id submitted twice → second call returns existing, no new row."""
        result1 = await create_submission(db_session, valid_payload)
        result2 = await create_submission(db_session, valid_payload)  # same client_submission_id
        assert result1.id == result2.id
        count = await db_session.scalar(select(func.count()).select_from(FeedbackSubmission))
        assert count == 1   # only one row created

    async def test_int_value_out_of_range_raises(self, db_session, active_questions):
        """int_value=6 for scale5 question raises FeedbackValidationError."""
        payload = build_payload(overrides={"answers[0].int_value": 6})
        with pytest.raises(FeedbackValidationError, match="int_value"):
            await create_submission(db_session, payload)

    async def test_unknown_question_id_raises(self, db_session, active_questions):
        """Payload referencing non-existent question_id raises FeedbackValidationError."""
        ...

    async def test_inactive_question_id_raises(self, db_session, active_questions):
        """Payload referencing is_active=False question raises FeedbackValidationError."""
        ...

    async def test_missing_required_question_raises(self, db_session, active_questions):
        """Omitting a non-text active question raises FeedbackValidationError."""
        ...

    async def test_text_value_over_500_chars_raises(self, db_session, active_questions):
        ...

    async def test_free_text_is_encrypted_at_rest(self, db_session, active_questions):
        """text_value stored in DB is not plaintext (encrypted bytes)."""
        await create_submission(db_session, valid_payload_with_text)
        raw = await db_session.scalar(
            select(FeedbackAnswer.text_value).where(FeedbackAnswer.submission_id == ...)
        )
        assert raw != b"Hoitajat olivat mukavia"   # must not be plaintext
        assert len(raw) > 20                        # has encryption overhead
```

---

## 3. Security tests — must all pass before deploy

```python
# tests/security/test_auth_security.py

class TestAuthSecurity:

    async def test_login_wrong_password_returns_generic_401(self, client):
        """Invalid credentials return 401 with generic message — no detail."""
        resp = await client.post("/api/v1/auth/login",
                                 json={"email": "staff@soite.fi", "password": "wrong"})
        assert resp.status_code == 401
        body = resp.json()
        assert "error" in body
        # Must NOT reveal whether email exists
        assert "email" not in body["error"]["message"].lower()
        assert "not found" not in body["error"]["message"].lower()

    async def test_login_nonexistent_email_same_timing_as_wrong_password(self, client):
        """Non-existent email response time ≈ wrong password response time (anti-enumeration)."""
        import time
        t1 = time.perf_counter()
        await client.post("/api/v1/auth/login",
                          json={"email": "nobody@soite.fi", "password": "x"})
        t2 = time.perf_counter()
        await client.post("/api/v1/auth/login",
                          json={"email": "staff@soite.fi", "password": "x"})
        t3 = time.perf_counter()
        # Both should be > 100ms (bcrypt) and within 50ms of each other
        assert (t2 - t1) > 0.1
        assert abs((t2 - t1) - (t3 - t2)) < 0.05

    async def test_rate_limit_on_auth_endpoint(self, client):
        """6th login attempt within 15 minutes returns 429."""
        for _ in range(5):
            await client.post("/api/v1/auth/login",
                              json={"email": "x@x.fi", "password": "x"})
        resp = await client.post("/api/v1/auth/login",
                                 json={"email": "x@x.fi", "password": "x"})
        assert resp.status_code == 429

    async def test_staff_cannot_access_admin_endpoints(self, client, staff_token):
        """JWT with role=staff → 403 on admin endpoints."""
        resp = await client.get("/api/v1/admin/questions",
                                headers={"Authorization": f"Bearer {staff_token}"})
        assert resp.status_code == 403

    async def test_anonymous_cannot_access_dashboard(self, client):
        """No JWT → 401 on dashboard endpoints."""
        resp = await client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 401

    async def test_expired_access_token_rejected(self, client, expired_token):
        """Expired JWT → 401."""
        resp = await client.get("/api/v1/dashboard/summary",
                                headers={"Authorization": f"Bearer {expired_token}"})
        assert resp.status_code == 401

    async def test_tampered_jwt_payload_rejected(self, client, valid_token):
        """Modifying JWT payload (e.g. role=admin) without valid signature → 401."""
        import base64, json
        header, payload_b64, sig = valid_token.split(".")
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=="))
        payload["role"] = "admin"
        tampered_payload = base64.urlsafe_b64encode(
            json.dumps(payload).encode()).decode().rstrip("=")
        tampered_token = f"{header}.{tampered_payload}.{sig}"
        resp = await client.get("/api/v1/admin/questions",
                                headers={"Authorization": f"Bearer {tampered_token}"})
        assert resp.status_code == 401

    async def test_revoked_refresh_token_triggers_full_session_revocation(self, client, db_session):
        """Presenting an already-rotated refresh token → ALL sessions for user revoked."""
        # Login, get refresh token
        login_resp = await client.post("/api/v1/auth/login", json=VALID_CREDS)
        old_refresh = login_resp.cookies["__Host-refresh_token"]

        # Rotate once (legitimate)
        await client.post("/api/v1/auth/refresh")

        # Now present the old (revoked) refresh token — simulates theft
        client.cookies.set("__Host-refresh_token", old_refresh)
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401

        # All sessions for this user should now be revoked
        active_tokens = await get_active_tokens_for_user(db_session, USER_ID)
        assert len(active_tokens) == 0

    async def test_sql_injection_in_feedback_payload(self, client):
        """SQL injection attempt in text_value is stored safely (not executed)."""
        payload = build_feedback_payload(text_value="'; DROP TABLE feedback_submissions; --")
        resp = await client.post("/api/v1/feedback", json=payload)
        assert resp.status_code == 200
        # Table must still exist
        count = await get_submission_count()
        assert count >= 1

    async def test_xss_in_free_text_is_stripped(self, client, admin_token):
        """HTML/script tags in free text are stripped before storage."""
        payload = build_feedback_payload(text_value="<script>alert(1)</script>Nice care")
        await client.post("/api/v1/feedback", json=payload)
        # Retrieve via staff dashboard
        resp = await client.get("/api/v1/dashboard/freetext?question_id=...",
                                headers={"Authorization": f"Bearer {admin_token}"})
        texts = [item["text"] for item in resp.json()["items"]]
        assert all("<script>" not in t for t in texts)
        assert any("Nice care" in t for t in texts)

    async def test_security_headers_present_on_all_responses(self, client):
        """Every response must include required security headers."""
        resp = await client.get("/health")
        assert "strict-transport-security" in resp.headers
        assert "x-content-type-options" in resp.headers
        assert "x-frame-options" in resp.headers
        assert "content-security-policy" in resp.headers

    async def test_feedback_rate_limit(self, client):
        """4th submission from same device within one hour → 429."""
        device_token = str(uuid.uuid4())
        for _ in range(3):
            await submit_feedback(client, device_token)
        resp = await submit_feedback(client, device_token)
        assert resp.status_code == 429
```

---

## 4. Integration tests — with real database

```python
# tests/integration/test_full_submission_flow.py
# Uses testcontainers-python to spin up a real PostgreSQL instance

import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def real_db():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg.get_connection_url()

class TestFullSubmissionFlow:

    async def test_submit_then_appear_in_dashboard(self, real_db):
        """Submit feedback → appears in staff dashboard summary."""
        ...

    async def test_offline_queue_drains_on_reconnect(self):
        """Simulate offline → queue submissions → reconnect → all submitted."""
        ...

    async def test_data_retention_purge_job(self, real_db):
        """Purge job removes submissions older than 3 years, keeps newer ones."""
        ...
```

---

## 5. Accessibility tests (automated)

```bash
# Run axe-core accessibility check on kiosk page
npx @axe-core/cli http://localhost:3000 --rules wcag2a,wcag2aa
```

Add to CI — fails if any WCAG 2.1 AA violations found.

---

## 6. Load test

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class TabletUser(HttpUser):
    wait_time = between(30, 120)  # patients take 30–120 seconds to fill form

    @task
    def submit_feedback(self):
        self.client.post("/api/v1/feedback", json=VALID_PAYLOAD,
                         headers={"X-Device-Token": str(uuid.uuid4())})

# Run: locust -f tests/load/locustfile.py --host http://localhost:8000
# Target: 10 concurrent tablets, p95 latency < 300ms
```

---

## 7. Factory definitions

```python
# tests/factories.py
import factory
from factory.alchemy import SQLAlchemyModelFactory
from app.models.question import Question
from app.models.feedback import FeedbackSubmission, FeedbackAnswer

class QuestionFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Question
    text_fi = factory.Faker("sentence", locale="fi_FI")
    text_en = factory.Faker("sentence")
    question_type = "scale5"
    display_order = factory.Sequence(lambda n: n)
    is_active = True

class FeedbackSubmissionFactory(SQLAlchemyModelFactory):
    class Meta:
        model = FeedbackSubmission
    client_submission_id = factory.LazyFunction(uuid.uuid4)
    device_token = factory.LazyFunction(uuid.uuid4)
    question_count = 3
    app_version = "1.0.0"
```
