"""Password hashing and verification with timing-attack mitigations.

bcrypt cost=12 — verified against OWASP recommendations for 2024.
DUMMY_HASH computed once at startup so non-existent user lookups
take the same time as wrong-password lookups (prevents account enumeration).
"""

import re

from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

DUMMY_HASH: str = _pwd_context.hash("soite-dummy-password-for-timing-safety")

_PASSWORD_POLICY = re.compile(
    r"^(?=.*[A-Z])(?=.*\d).{12,}$"
)


def hash_password(password: str) -> str:
    """Return bcrypt hash of password."""
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time verify plain password against stored hash."""
    return _pwd_context.verify(plain, hashed)


def verify_password_timing_safe(plain: str, hashed: str | None) -> bool:
    """Always run bcrypt even when hashed is None (prevents timing-based enumeration)."""
    return _pwd_context.verify(plain, hashed if hashed is not None else DUMMY_HASH)


def validate_password_policy(password: str) -> bool:
    """Return True if password meets policy: 12+ chars, ≥1 uppercase, ≥1 digit."""
    return bool(_PASSWORD_POLICY.match(password))
