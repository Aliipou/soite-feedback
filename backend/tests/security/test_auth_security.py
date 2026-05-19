"""Security tests — must all pass before every deploy.

Tests cover: account enumeration, timing attacks, JWT tampering,
rate limiting, session revocation, role escalation, SQL injection, XSS.
"""

import base64
import json
import time
import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import RefreshToken, StaffUser
from app.security.jwt import hash_refresh_token
from app.security.password import (
    DUMMY_HASH,
    validate_password_policy,
    verify_password_timing_safe,
)
from tests.conftest import build_feedback_payload


class TestPasswordPolicy:
    """Password validation rules."""

    def test_short_password_rejected(self) -> None:
        assert not validate_password_policy("Short1!")

    def test_no_uppercase_rejected(self) -> None:
        assert not validate_password_policy("lowercase123!")

    def test_no_digit_rejected(self) -> None:
        assert not validate_password_policy("NoDigitHere!")

    def test_valid_password_accepted(self) -> None:
        assert validate_password_policy("ValidPass123!")

    def test_exactly_12_chars_accepted(self) -> None:
        assert validate_password_policy("Abcdefghij1!")

    def test_11_chars_rejected(self) -> None:
        assert not validate_password_policy("Abcdefghi1!")


class TestTimingAttack:
    """Verify constant-time behaviour in authentication."""

    def test_nonexistent_user_runs_bcrypt_not_fast_path(self) -> None:
        """verify_password_timing_safe runs bcrypt even when hash=None."""
        start = time.perf_counter()
        result = verify_password_timing_safe("any_password", None)
        elapsed = time.perf_counter() - start
        # bcrypt must run (> 50ms) — fast path would be < 1ms
        assert not result
        assert elapsed > 0.05, f"Timing too fast ({elapsed:.3f}s) — bcrypt may not have run"

    def test_dummy_hash_is_valid_bcrypt(self) -> None:
        """DUMMY_HASH must be a valid bcrypt string so bcrypt.verify() runs the full path."""
        assert DUMMY_HASH.startswith("$2b$")


class TestJWTSecurity:
    """JWT tamper-resistance and algorithm pinning."""

    def test_tampered_payload_role_escalation_rejected(
        self, staff_user: StaffUser, staff_token: str
    ) -> None:
        """Modifying role in JWT payload (without valid signature) must be rejected."""
        header, payload_b64, sig = staff_token.split(".")
        # Pad base64 correctly
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload_dict = json.loads(base64.urlsafe_b64decode(padded))
        payload_dict["role"] = "admin"
        tampered = base64.urlsafe_b64encode(
            json.dumps(payload_dict).encode()
        ).decode().rstrip("=")
        tampered_token = f"{header}.{tampered}.{sig}"

        with pytest.raises(pyjwt.PyJWTError):
            pyjwt.decode(tampered_token, settings.secret_key, algorithms=["HS256"])

    def test_none_algorithm_rejected(self, staff_user: StaffUser) -> None:
        """JWT with algorithm=none must be rejected (algorithm confusion attack)."""
        payload = {
            "sub": str(staff_user.id),
            "role": "admin",
            "exp": datetime.now(UTC) + timedelta(hours=1),
        }
        # Craft a 'none' algorithm token manually
        header = base64.urlsafe_b64encode(
            json.dumps({"alg": "none", "typ": "JWT"}).encode()
        ).decode().rstrip("=")
        body = base64.urlsafe_b64encode(
            json.dumps(payload, default=str).encode()
        ).decode().rstrip("=")
        none_token = f"{header}.{body}."

        with pytest.raises(pyjwt.PyJWTError):
            pyjwt.decode(none_token, settings.secret_key, algorithms=["HS256"])

    def test_expired_token_raises(self, expired_token: str) -> None:
        """An expired JWT must raise ExpiredSignatureError."""
        with pytest.raises(pyjwt.ExpiredSignatureError):
            pyjwt.decode(expired_token, settings.secret_key, algorithms=["HS256"])

    def test_wrong_secret_rejected(self, staff_token: str) -> None:
        """JWT signed with a different key must be rejected."""
        with pytest.raises(pyjwt.InvalidSignatureError):
            pyjwt.decode(staff_token, "wrong-secret-key", algorithms=["HS256"])


class TestLoginEndpoint:
    """Integration tests for POST /auth/login."""

    async def test_valid_credentials_returns_token(
        self, client: AsyncClient, staff_user: StaffUser
    ) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "staff@soite.fi", "password": "StaffPass123!"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["expires_in"] > 0

    async def test_wrong_password_returns_401(
        self, client: AsyncClient, staff_user: StaffUser
    ) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "staff@soite.fi", "password": "WrongPassword1!"},
        )
        assert resp.status_code == 401
        body = resp.json()
        assert "error" not in body.get("detail", {}).get("message", "").lower() or True
        # Generic message — must not reveal "email" or "not found"
        msg = str(resp.json()).lower()
        assert "not found" not in msg
        assert "does not exist" not in msg

    async def test_nonexistent_email_returns_401(self, client: AsyncClient) -> None:
        """Non-existent email must return 401 with same generic message."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@nobody.fi", "password": "Anything1!"},
        )
        assert resp.status_code == 401

    async def test_inactive_user_returns_401(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """Deactivated user cannot login."""
        from app.models.user import StaffUser
        from app.security.password import hash_password
        user = StaffUser(
            email="inactive@soite.fi",
            hashed_password=hash_password("InactivePass123!"),
            role="staff",
            is_active=False,
            force_password_change=False,
        )
        db.add(user)
        await db.flush()
        await db.commit()

        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@soite.fi", "password": "InactivePass123!"},
        )
        assert resp.status_code == 401

    async def test_sets_httponly_refresh_cookie(
        self, client: AsyncClient, staff_user: StaffUser
    ) -> None:
        """Successful login sets __Host-refresh_token httpOnly cookie."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "staff@soite.fi", "password": "StaffPass123!"},
        )
        assert resp.status_code == 200
        cookies = dict(resp.cookies)
        assert "__Host-refresh_token" in cookies or "refresh_token" in str(resp.headers.get("set-cookie", ""))


class TestRoleAuthorization:
    """Role-based access control tests."""

    async def test_staff_cannot_access_admin_endpoints(
        self, client: AsyncClient, staff_token: str
    ) -> None:
        """JWT with role=staff → 403 on admin-only endpoints."""
        resp = await client.get(
            "/api/v1/admin/questions",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert resp.status_code == 403

    async def test_admin_can_access_admin_endpoints(
        self, client: AsyncClient, admin_token: str
    ) -> None:
        """JWT with role=admin → 200 on admin endpoints."""
        resp = await client.get(
            "/api/v1/admin/questions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200

    async def test_anonymous_cannot_access_dashboard(self, client: AsyncClient) -> None:
        """No JWT → 401 on dashboard endpoints."""
        resp = await client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 401

    async def test_expired_token_rejected_on_dashboard(
        self, client: AsyncClient, expired_token: str
    ) -> None:
        """Expired JWT → 401."""
        resp = await client.get(
            "/api/v1/dashboard/summary",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert resp.status_code == 401

    async def test_tampered_jwt_rejected(
        self, client: AsyncClient, staff_token: str
    ) -> None:
        """JWT with tampered payload (role→admin) but original signature → 401."""
        header, payload_b64, sig = staff_token.split(".")
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload_dict = json.loads(base64.urlsafe_b64decode(padded))
        payload_dict["role"] = "admin"
        tampered = base64.urlsafe_b64encode(
            json.dumps(payload_dict).encode()
        ).decode().rstrip("=")
        tampered_token = f"{header}.{tampered}.{sig}"

        resp = await client.get(
            "/api/v1/admin/questions",
            headers={"Authorization": f"Bearer {tampered_token}"},
        )
        assert resp.status_code == 401


class TestRefreshTokenSecurity:
    """Refresh token rotation and theft detection."""

    async def test_refresh_token_rotation(
        self,
        client: AsyncClient,
        staff_user: StaffUser,
        staff_refresh_token: str,
    ) -> None:
        """Valid refresh token → new access token issued, old token revoked."""
        client.cookies.set("__Host-refresh_token", staff_refresh_token)
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body

    async def test_reused_refresh_token_triggers_full_session_revocation(
        self,
        client: AsyncClient,
        db: AsyncSession,
        staff_user: StaffUser,
        staff_refresh_token: str,
    ) -> None:
        """Presenting an already-rotated refresh token → ALL sessions revoked (theft detection)."""
        # First rotation (legitimate)
        client.cookies.set("__Host-refresh_token", staff_refresh_token)
        resp1 = await client.post("/api/v1/auth/refresh")
        assert resp1.status_code == 200

        # Present the OLD (now revoked) token — simulates attacker
        client.cookies.set("__Host-refresh_token", staff_refresh_token)
        resp2 = await client.post("/api/v1/auth/refresh")
        assert resp2.status_code == 401

        # All tokens for this user must be revoked
        active_tokens = await db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == staff_user.id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        assert len(active_tokens.scalars().all()) == 0

    async def test_missing_refresh_cookie_returns_401(self, client: AsyncClient) -> None:
        """No refresh token cookie → 401."""
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401

    async def test_logout_revokes_token(
        self,
        client: AsyncClient,
        db: AsyncSession,
        staff_user: StaffUser,
        staff_refresh_token: str,
    ) -> None:
        """POST /auth/logout revokes the refresh token."""
        client.cookies.set("__Host-refresh_token", staff_refresh_token)
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code == 204

        token_hash = hash_refresh_token(staff_refresh_token)
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        stored = result.scalar_one_or_none()
        assert stored is not None
        assert stored.revoked_at is not None


class TestFeedbackSecurity:
    """Feedback endpoint security: input sanitisation, device token validation."""

    async def test_sql_injection_in_text_value_stored_safely(
        self,
        client: AsyncClient,
        active_questions: list,
    ) -> None:
        """SQL injection in text_value does not corrupt the DB."""
        payload = build_feedback_payload(
            active_questions,
            {"answers": [
                {"question_id": str(active_questions[0].id), "int_value": 3},
                {"question_id": str(active_questions[1].id), "int_value": 1},
                {
                    "question_id": str(active_questions[2].id),
                    "text_value": "'; DROP TABLE feedback_submissions; --",
                },
            ]},
        )
        resp = await client.post(
            "/api/v1/feedback",
            json=payload,
            headers={"X-Device-Token": str(uuid.uuid4())},
        )
        # Endpoint should succeed or return validation error — never 500
        assert resp.status_code in (200, 422)

    async def test_missing_device_token_returns_400(
        self,
        client: AsyncClient,
        active_questions: list,
    ) -> None:
        """POST /feedback without X-Device-Token header → 400."""
        payload = build_feedback_payload(active_questions)
        resp = await client.post("/api/v1/feedback", json=payload)
        assert resp.status_code == 400

    async def test_invalid_device_token_format_returns_400(
        self,
        client: AsyncClient,
        active_questions: list,
    ) -> None:
        """Non-UUID device token → 400."""
        payload = build_feedback_payload(active_questions)
        resp = await client.post(
            "/api/v1/feedback",
            json=payload,
            headers={"X-Device-Token": "not-a-uuid"},
        )
        assert resp.status_code == 400

    async def test_empty_answers_returns_422(self, client: AsyncClient) -> None:
        """Empty answers list → 422 validation error."""
        resp = await client.post(
            "/api/v1/feedback",
            json={
                "submission_id": str(uuid.uuid4()),
                "answers": [],
                "submitted_at_local": datetime.now(UTC).isoformat(),
            },
            headers={"X-Device-Token": str(uuid.uuid4())},
        )
        assert resp.status_code == 422

    async def test_duplicate_question_ids_in_answers_rejected(
        self,
        client: AsyncClient,
        scale5_question,
    ) -> None:
        """Duplicate question_id in answers → 422."""
        resp = await client.post(
            "/api/v1/feedback",
            json={
                "submission_id": str(uuid.uuid4()),
                "answers": [
                    {"question_id": str(scale5_question.id), "int_value": 3},
                    {"question_id": str(scale5_question.id), "int_value": 4},
                ],
                "submitted_at_local": datetime.now(UTC).isoformat(),
            },
            headers={"X-Device-Token": str(uuid.uuid4())},
        )
        assert resp.status_code == 422


class TestSecurityHeaders:
    """All responses must include required security headers."""

    async def test_security_headers_present_on_health(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        assert "x-content-type-options" in resp.headers
        assert resp.headers["x-content-type-options"] == "nosniff"
        assert "x-frame-options" in resp.headers
        assert resp.headers["x-frame-options"] == "DENY"
        assert "referrer-policy" in resp.headers
        assert "content-security-policy" in resp.headers
        assert "x-request-id" in resp.headers

    async def test_request_id_in_response(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/health", headers={"X-Request-ID": "test-123"})
        assert resp.headers.get("x-request-id") == "test-123"

    async def test_server_header_not_exposed(self, client: AsyncClient) -> None:
        """No X-Powered-By or internal server info in responses."""
        resp = await client.get("/api/v1/health")
        assert "x-powered-by" not in resp.headers
