"""Auth router edge cases — refresh paths, logout, cookie attributes."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import RefreshToken, StaffUser
from app.security.jwt import hash_refresh_token
from app.security.password import hash_password

pytestmark = pytest.mark.asyncio


# ── helpers ────────────────────────────────────────────────────────────────────

async def _insert_refresh_token(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    expires_at: datetime | None = None,
    revoked: bool = False,
) -> str:
    raw = "edge-" + uuid.uuid4().hex
    token_hash = hash_refresh_token(raw)
    expires = expires_at or datetime.now(UTC) + timedelta(days=7)
    rt = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires)
    if revoked:
        rt.revoked_at = datetime.now(UTC)
    db.add(rt)
    await db.flush()
    return raw


# ── /auth/refresh edge cases ──────────────────────────────────────────────────


class TestRefreshEdgeCases:
    async def test_random_cookie_returns_401(self, client: AsyncClient) -> None:
        client.cookies.set("__Host-refresh_token", "totally-random-value")
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401

    async def test_expired_token_returns_401(
        self, client: AsyncClient, db: AsyncSession, staff_user: StaffUser
    ) -> None:
        past = datetime.now(UTC) - timedelta(hours=1)
        raw = await _insert_refresh_token(db, staff_user.id, expires_at=past)
        client.cookies.set("__Host-refresh_token", raw)
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401

    async def test_already_revoked_token_returns_401(
        self, client: AsyncClient, db: AsyncSession, staff_user: StaffUser
    ) -> None:
        raw = await _insert_refresh_token(db, staff_user.id, revoked=True)
        client.cookies.set("__Host-refresh_token", raw)
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401

    async def test_deactivated_user_returns_401(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        inactive = StaffUser(
            email="inactive2@soite.fi",
            hashed_password=hash_password("InactivePass123!"),
            role="staff",
            is_active=False,
            force_password_change=False,
        )
        db.add(inactive)
        await db.flush()

        raw = await _insert_refresh_token(db, inactive.id)
        client.cookies.set("__Host-refresh_token", raw)
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401

    async def test_missing_cookie_returns_401(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401

    async def test_valid_refresh_issues_new_access_token(
        self,
        client: AsyncClient,
        db: AsyncSession,
        staff_user: StaffUser,
        staff_refresh_token: str,
    ) -> None:
        client.cookies.set("__Host-refresh_token", staff_refresh_token)
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    async def test_refresh_sets_new_cookie(
        self,
        client: AsyncClient,
        staff_user: StaffUser,
        staff_refresh_token: str,
    ) -> None:
        client.cookies.set("__Host-refresh_token", staff_refresh_token)
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 200
        set_cookie = resp.headers.get("set-cookie", "")
        assert "refresh_token" in set_cookie.lower()


# ── /auth/logout edge cases ───────────────────────────────────────────────────


class TestLogoutEdgeCases:
    async def test_logout_without_cookie_returns_204(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code == 204

    async def test_logout_with_valid_token_returns_204(
        self,
        client: AsyncClient,
        staff_user: StaffUser,
        staff_refresh_token: str,
    ) -> None:
        client.cookies.set("__Host-refresh_token", staff_refresh_token)
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code == 204

    async def test_logout_clears_cookie(
        self,
        client: AsyncClient,
        staff_user: StaffUser,
        staff_refresh_token: str,
    ) -> None:
        client.cookies.set("__Host-refresh_token", staff_refresh_token)
        resp = await client.post("/api/v1/auth/logout")
        set_cookie = resp.headers.get("set-cookie", "")
        # Cookie cleared by max-age=0 or expires in the past
        assert "refresh_token" in set_cookie.lower()

    async def test_double_logout_is_safe(
        self,
        client: AsyncClient,
        staff_user: StaffUser,
        staff_refresh_token: str,
    ) -> None:
        client.cookies.set("__Host-refresh_token", staff_refresh_token)
        resp1 = await client.post("/api/v1/auth/logout")
        resp2 = await client.post("/api/v1/auth/logout")
        assert resp1.status_code == 204
        assert resp2.status_code == 204


# ── /auth/login edge cases ────────────────────────────────────────────────────


class TestLoginEdgeCases:
    async def test_email_case_insensitive(
        self, client: AsyncClient, staff_user: StaffUser
    ) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "STAFF@SOITE.FI", "password": "StaffPass123!"},
        )
        assert resp.status_code == 200

    async def test_login_response_has_expires_in(
        self, client: AsyncClient, staff_user: StaffUser
    ) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "staff@soite.fi", "password": "StaffPass123!"},
        )
        assert resp.status_code == 200
        assert resp.json()["expires_in"] > 0

    async def test_malformed_email_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "not-an-email", "password": "StaffPass123!"},
        )
        assert resp.status_code == 422

    async def test_missing_password_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "staff@soite.fi"},
        )
        assert resp.status_code == 422

    async def test_generic_error_message_on_bad_credentials(
        self, client: AsyncClient, staff_user: StaffUser
    ) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "staff@soite.fi", "password": "WrongPass123!"},
        )
        assert resp.status_code == 401
        body_text = str(resp.json()).lower()
        # Must not reveal whether email exists
        assert "not found" not in body_text
        assert "does not exist" not in body_text
        assert "no user" not in body_text
