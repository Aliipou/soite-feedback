"""Unit tests for authentication service — tokens, rotation, revocation."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import RefreshToken, StaffUser
from app.security.jwt import hash_refresh_token
from app.security.password import hash_password
from app.services.auth import (
    authenticate_user,
    build_token_response,
    create_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
    update_last_login,
)

pytestmark = pytest.mark.asyncio


# ── helpers ────────────────────────────────────────────────────────────────────

async def _make_refresh_token(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    expires_at: datetime | None = None,
    revoked: bool = False,
) -> str:
    raw = "test-" + uuid.uuid4().hex
    token_hash = hash_refresh_token(raw)
    expires = expires_at or datetime.now(UTC) + timedelta(days=7)
    rt = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires,
    )
    if revoked:
        rt.revoked_at = datetime.now(UTC)
    db.add(rt)
    await db.flush()
    return raw


# ── authenticate_user ─────────────────────────────────────────────────────────


class TestAuthenticateUser:
    async def test_valid_credentials_return_user(
        self, db: AsyncSession, staff_user: StaffUser
    ) -> None:
        user = await authenticate_user(db, "staff@soite.fi", "StaffPass123!")
        assert user is not None
        assert user.id == staff_user.id

    async def test_email_normalised_to_lowercase(
        self, db: AsyncSession, staff_user: StaffUser
    ) -> None:
        user = await authenticate_user(db, "STAFF@SOITE.FI", "StaffPass123!")
        assert user is not None

    async def test_wrong_password_returns_none(
        self, db: AsyncSession, staff_user: StaffUser
    ) -> None:
        user = await authenticate_user(db, "staff@soite.fi", "WrongPassword1!")
        assert user is None

    async def test_nonexistent_email_returns_none(self, db: AsyncSession) -> None:
        user = await authenticate_user(db, "nobody@example.com", "AnyPass123!")
        assert user is None

    async def test_inactive_user_returns_none(self, db: AsyncSession) -> None:
        inactive = StaffUser(
            email="inactive@soite.fi",
            hashed_password=hash_password("InactivePass123!"),
            role="staff",
            is_active=False,
            force_password_change=False,
        )
        db.add(inactive)
        await db.flush()

        user = await authenticate_user(db, "inactive@soite.fi", "InactivePass123!")
        assert user is None


# ── create_refresh_token ──────────────────────────────────────────────────────


class TestCreateRefreshToken:
    async def test_returns_raw_token_string(
        self, db: AsyncSession, staff_user: StaffUser
    ) -> None:
        raw = await create_refresh_token(db, staff_user.id)
        assert isinstance(raw, str)
        assert len(raw) > 0

    async def test_token_stored_as_hash_in_db(
        self, db: AsyncSession, staff_user: StaffUser
    ) -> None:
        raw = await create_refresh_token(db, staff_user.id)
        token_hash = hash_refresh_token(raw)
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        stored = result.scalar_one_or_none()
        assert stored is not None
        assert stored.user_id == staff_user.id

    async def test_token_not_revoked_initially(
        self, db: AsyncSession, staff_user: StaffUser
    ) -> None:
        raw = await create_refresh_token(db, staff_user.id)
        token_hash = hash_refresh_token(raw)
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        stored = result.scalar_one_or_none()
        assert stored is not None
        assert stored.revoked_at is None

    async def test_multiple_tokens_can_coexist(
        self, db: AsyncSession, staff_user: StaffUser
    ) -> None:
        raw1 = await create_refresh_token(db, staff_user.id)
        raw2 = await create_refresh_token(db, staff_user.id)
        assert raw1 != raw2


# ── rotate_refresh_token ──────────────────────────────────────────────────────


class TestRotateRefreshToken:
    async def test_happy_path_returns_user_and_new_token(
        self, db: AsyncSession, staff_user: StaffUser
    ) -> None:
        raw = await _make_refresh_token(db, staff_user.id)
        user, new_raw = await rotate_refresh_token(db, raw)
        assert user.id == staff_user.id
        assert isinstance(new_raw, str)
        assert new_raw != raw

    async def test_old_token_revoked_after_rotation(
        self, db: AsyncSession, staff_user: StaffUser
    ) -> None:
        raw = await _make_refresh_token(db, staff_user.id)
        old_hash = hash_refresh_token(raw)
        await rotate_refresh_token(db, raw)

        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == old_hash)
        )
        stored = result.scalar_one_or_none()
        assert stored is not None
        assert stored.revoked_at is not None

    async def test_invalid_token_raises(self, db: AsyncSession) -> None:
        with pytest.raises(ValueError, match="Invalid"):
            await rotate_refresh_token(db, "this-token-does-not-exist")

    async def test_already_revoked_raises_and_wipes_all_sessions(
        self, db: AsyncSession, staff_user: StaffUser
    ) -> None:
        raw = await _make_refresh_token(db, staff_user.id, revoked=True)
        # Create an active token for the same user (simulates a live session)
        await _make_refresh_token(db, staff_user.id)

        with pytest.raises(ValueError, match="reuse"):
            await rotate_refresh_token(db, raw)

        # All sessions must be revoked (theft detection)
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == staff_user.id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        assert result.scalars().all() == []

    async def test_expired_token_raises(
        self, db: AsyncSession, staff_user: StaffUser
    ) -> None:
        past = datetime.now(UTC) - timedelta(days=1)
        raw = await _make_refresh_token(db, staff_user.id, expires_at=past)
        with pytest.raises(ValueError, match="expired"):
            await rotate_refresh_token(db, raw)

    async def test_deactivated_user_raises(self, db: AsyncSession) -> None:
        inactive = StaffUser(
            email="gone@soite.fi",
            hashed_password=hash_password("InactivePass123!"),
            role="staff",
            is_active=False,
            force_password_change=False,
        )
        db.add(inactive)
        await db.flush()

        raw = await _make_refresh_token(db, inactive.id)
        with pytest.raises(ValueError, match="deactivated"):
            await rotate_refresh_token(db, raw)


# ── revoke_refresh_token ──────────────────────────────────────────────────────


class TestRevokeRefreshToken:
    async def test_marks_token_as_revoked(
        self, db: AsyncSession, staff_user: StaffUser
    ) -> None:
        raw = await _make_refresh_token(db, staff_user.id)
        await revoke_refresh_token(db, raw)

        token_hash = hash_refresh_token(raw)
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        stored = result.scalar_one_or_none()
        assert stored is not None
        assert stored.revoked_at is not None

    async def test_revoking_unknown_token_is_noop(self, db: AsyncSession) -> None:
        # Should not raise even if the token doesn't exist
        await revoke_refresh_token(db, "nonexistent-token")


# ── update_last_login ─────────────────────────────────────────────────────────


class TestUpdateLastLogin:
    async def test_sets_last_login_at(
        self, db: AsyncSession, staff_user: StaffUser
    ) -> None:
        assert staff_user.last_login_at is None
        before = datetime.now(UTC)
        await update_last_login(db, staff_user)
        assert staff_user.last_login_at is not None
        assert staff_user.last_login_at >= before

    async def test_second_call_updates_timestamp(
        self, db: AsyncSession, staff_user: StaffUser
    ) -> None:
        await update_last_login(db, staff_user)
        first_ts = staff_user.last_login_at
        await update_last_login(db, staff_user)
        assert staff_user.last_login_at >= first_ts  # type: ignore[operator]


# ── build_token_response ──────────────────────────────────────────────────────


class TestBuildTokenResponse:
    def test_contains_required_keys(self, staff_user: StaffUser) -> None:
        resp = build_token_response(staff_user)
        assert "access_token" in resp
        assert "token_type" in resp
        assert "expires_in" in resp

    def test_token_type_is_bearer(self, staff_user: StaffUser) -> None:
        resp = build_token_response(staff_user)
        assert resp["token_type"] == "bearer"

    def test_expires_in_is_positive(self, staff_user: StaffUser) -> None:
        resp = build_token_response(staff_user)
        assert resp["expires_in"] > 0

    def test_access_token_is_string(self, staff_user: StaffUser) -> None:
        resp = build_token_response(staff_user)
        assert isinstance(resp["access_token"], str)
        assert len(resp["access_token"]) > 20
