"""Unit tests for JWT and password primitive functions."""

import time
import uuid

import jwt as pyjwt
import pytest

from app.config import settings
from app.security.jwt import (
    create_access_token,
    create_raw_refresh_token,
    decode_access_token,
    hash_refresh_token,
)
from app.security.password import (
    hash_password,
    validate_password_policy,
    verify_password,
    verify_password_timing_safe,
)

pytestmark = pytest.mark.asyncio


# ── JWT primitives ─────────────────────────────────────────────────────────────


class TestCreateAccessToken:
    def test_returns_decodable_token(self) -> None:
        token = create_access_token(subject=str(uuid.uuid4()), role="staff")
        payload = pyjwt.decode(token, settings.secret_key, algorithms=["HS256"])
        assert "sub" in payload
        assert "role" in payload
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload

    def test_subject_and_role_embedded(self) -> None:
        sub = str(uuid.uuid4())
        token = create_access_token(subject=sub, role="admin")
        payload = pyjwt.decode(token, settings.secret_key, algorithms=["HS256"])
        assert payload["sub"] == sub
        assert payload["role"] == "admin"

    def test_extra_claims_embedded(self) -> None:
        token = create_access_token(
            subject=str(uuid.uuid4()), role="staff", extra={"custom": "value"}
        )
        payload = pyjwt.decode(token, settings.secret_key, algorithms=["HS256"])
        assert payload["custom"] == "value"

    def test_extra_none_does_not_crash(self) -> None:
        token = create_access_token(subject=str(uuid.uuid4()), role="staff", extra=None)
        assert isinstance(token, str)

    def test_jti_is_unique_per_call(self) -> None:
        t1 = create_access_token(subject=str(uuid.uuid4()), role="staff")
        t2 = create_access_token(subject=str(uuid.uuid4()), role="staff")
        p1 = pyjwt.decode(t1, settings.secret_key, algorithms=["HS256"])
        p2 = pyjwt.decode(t2, settings.secret_key, algorithms=["HS256"])
        assert p1["jti"] != p2["jti"]


class TestDecodeAccessToken:
    def test_decodes_valid_token(self) -> None:
        sub = str(uuid.uuid4())
        token = create_access_token(subject=sub, role="staff")
        payload = decode_access_token(token)
        assert payload["sub"] == sub

    def test_raises_on_invalid_signature(self) -> None:
        token = create_access_token(subject=str(uuid.uuid4()), role="staff")
        parts = token.split(".")
        tampered = parts[0] + "." + parts[1] + ".invalidsig"
        with pytest.raises(pyjwt.PyJWTError):
            decode_access_token(tampered)

    def test_raises_on_wrong_secret(self) -> None:
        import jwt

        wrong_token = jwt.encode({"sub": "x", "role": "staff"}, "wrong-key", algorithm="HS256")
        with pytest.raises(pyjwt.PyJWTError):
            decode_access_token(wrong_token)


class TestCreateRawRefreshToken:
    def test_returns_128_char_hex_string(self) -> None:
        raw = create_raw_refresh_token()
        assert len(raw) == 128
        assert all(c in "0123456789abcdef" for c in raw)

    def test_unique_per_call(self) -> None:
        r1 = create_raw_refresh_token()
        r2 = create_raw_refresh_token()
        assert r1 != r2


class TestHashRefreshToken:
    def test_returns_64_char_hex(self) -> None:
        digest = hash_refresh_token("some-token")
        assert len(digest) == 64
        assert all(c in "0123456789abcdef" for c in digest)

    def test_deterministic(self) -> None:
        token = "deterministic-test-token"
        assert hash_refresh_token(token) == hash_refresh_token(token)

    def test_different_inputs_different_digests(self) -> None:
        assert hash_refresh_token("token-a") != hash_refresh_token("token-b")


# ── Password primitives ────────────────────────────────────────────────────────


class TestHashPassword:
    def test_returns_bcrypt_string(self) -> None:
        h = hash_password("SomePassword1!")
        assert h.startswith("$2b$")

    def test_different_hash_per_call(self) -> None:
        # bcrypt uses random salt
        h1 = hash_password("SomePassword1!")
        h2 = hash_password("SomePassword1!")
        assert h1 != h2


class TestVerifyPassword:
    def test_correct_password_returns_true(self) -> None:
        h = hash_password("CorrectPass1!")
        assert verify_password("CorrectPass1!", h) is True

    def test_wrong_password_returns_false(self) -> None:
        h = hash_password("CorrectPass1!")
        assert verify_password("WrongPass1!", h) is False


class TestVerifyPasswordTimingSafe:
    def test_correct_password_and_hash_returns_true(self) -> None:
        h = hash_password("ValidPass123!")
        assert verify_password_timing_safe("ValidPass123!", h) is True

    def test_wrong_password_returns_false(self) -> None:
        h = hash_password("ValidPass123!")
        assert verify_password_timing_safe("WrongPass123!", h) is False

    def test_none_hash_returns_false_and_runs_bcrypt(self) -> None:
        start = time.perf_counter()
        result = verify_password_timing_safe("anything", None)
        elapsed = time.perf_counter() - start
        assert result is False
        # bcrypt must have run (prevents fast-path timing leak)
        assert elapsed > 0.05


class TestValidatePasswordPolicy:
    def test_valid_password_accepted(self) -> None:
        assert validate_password_policy("ValidPass123!") is True

    def test_too_short_rejected(self) -> None:
        assert validate_password_policy("Short1!") is False

    def test_no_uppercase_rejected(self) -> None:
        assert validate_password_policy("lowercase123!") is False

    def test_no_digit_rejected(self) -> None:
        assert validate_password_policy("NoDigitHereABC!") is False

    def test_exactly_12_chars_accepted(self) -> None:
        assert validate_password_policy("Abcdefghij1!") is True

    def test_11_chars_rejected(self) -> None:
        assert validate_password_policy("Abcdefghi1!") is False
