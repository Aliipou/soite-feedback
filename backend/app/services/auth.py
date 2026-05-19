"""Authentication service — login, token rotation, theft detection."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import RefreshToken, StaffUser
from app.security.jwt import create_access_token, create_raw_refresh_token, hash_refresh_token
from app.security.password import verify_password_timing_safe


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> StaffUser | None:
    """Verify credentials. Always runs bcrypt to prevent timing-based enumeration.

    Returns the user on success, None on failure.
    """
    result = await db.execute(select(StaffUser).where(StaffUser.email == email.lower().strip()))
    user = result.scalar_one_or_none()

    hashed = user.hashed_password if user else None
    valid = verify_password_timing_safe(password, hashed)

    if not user or not valid or not user.is_active:
        return None
    return user


async def create_refresh_token(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> str:
    """Issue a new refresh token, store hash in DB, return raw token."""
    raw = create_raw_refresh_token()
    token_hash = hash_refresh_token(raw)
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)

    db.add(RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    ))
    await db.flush()
    return raw


async def rotate_refresh_token(
    db: AsyncSession,
    raw_token: str,
) -> tuple[StaffUser, str]:
    """Rotate a refresh token. Detects theft if token already revoked.

    Returns (user, new_raw_refresh_token).
    Raises ValueError on invalid/expired/revoked tokens.
    """
    token_hash = hash_refresh_token(raw_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    stored = result.scalar_one_or_none()

    if stored is None:
        raise ValueError("Invalid refresh token")

    if stored.revoked_at is not None:
        # Token already rotated — potential theft: revoke ALL sessions for this user
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == stored.user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
        raise ValueError("Token reuse detected — all sessions revoked")

    if stored.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        stored.revoked_at = datetime.now(UTC)
        raise ValueError("Refresh token expired")

    # Load user
    user_result = await db.execute(
        select(StaffUser).where(StaffUser.id == stored.user_id)
    )
    user = user_result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise ValueError("User not found or deactivated")

    # Revoke old token and issue new one
    stored.revoked_at = datetime.now(UTC)
    await db.flush()

    new_raw = await create_refresh_token(db, user.id)
    return user, new_raw


async def revoke_refresh_token(db: AsyncSession, raw_token: str) -> None:
    """Revoke a specific refresh token (logout)."""
    token_hash = hash_refresh_token(raw_token)
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == token_hash, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )


async def update_last_login(db: AsyncSession, user: StaffUser) -> None:
    """Record login timestamp on the user row."""
    user.last_login_at = datetime.now(UTC)
    await db.flush()


def build_token_response(user: StaffUser) -> dict:
    """Build the access_token response dict from a user object."""
    access_token = create_access_token(subject=str(user.id), role=user.role)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }
