"""JWT creation and verification.

Uses PyJWT with explicit algorithm pinning — prevents the 'none' algorithm attack.
Never use python-jose (abandoned, CVE-2024-33663).
"""

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.config import settings

ALGORITHM = "HS256"


def _now() -> datetime:
    return datetime.now(UTC)


def create_access_token(
    subject: str,
    role: str,
    extra: dict[str, Any] | None = None,
) -> str:
    """Return a signed JWT access token.

    Args:
        subject: User ID (UUID string).
        role: 'staff' or 'admin'.
        extra: Additional claims to embed.
    """
    expire = _now() + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "exp": expire,
        "iat": _now(),
        "jti": str(uuid.uuid4()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT access token.

    Raises jwt.PyJWTError on invalid/expired token.
    Always passes algorithms= explicitly to prevent algorithm confusion.
    """
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])  # type: ignore[return-value]


def create_raw_refresh_token() -> str:
    """Return a cryptographically random 64-byte hex refresh token."""
    return secrets.token_hex(64)


def hash_refresh_token(token: str) -> str:
    """Return SHA-256 hex digest of a refresh token for DB storage."""
    import hashlib

    return hashlib.sha256(token.encode()).hexdigest()
