"""Shared test fixtures — async DB session, HTTP client, user factories."""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.question import Question
from app.models.user import RefreshToken, StaffUser
from app.security.jwt import create_access_token, hash_refresh_token
from app.security.password import hash_password

# ── In-memory SQLite for unit/router tests (no Docker needed) ─────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True, scope="function")
async def setup_db() -> AsyncGenerator[None, None]:
    """Create all tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Yields an isolated async DB session per test."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client with the DB dependency overridden."""
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Fixtures: question helpers ─────────────────────────────────────────────────

@pytest_asyncio.fixture
async def scale5_question(db: AsyncSession) -> Question:
    q = Question(
        text_fi="Kuinka tyytyväinen olit?",
        question_type="scale5",
        display_order=1,
        is_active=True,
    )
    db.add(q)
    await db.flush()
    return q


@pytest_asyncio.fixture
async def yesno_question(db: AsyncSession) -> Question:
    q = Question(
        text_fi="Saitko riittävästi tietoa?",
        question_type="yesno",
        display_order=2,
        is_active=True,
    )
    db.add(q)
    await db.flush()
    return q


@pytest_asyncio.fixture
async def text_question(db: AsyncSession) -> Question:
    q = Question(
        text_fi="Muuta palautetta?",
        question_type="text",
        display_order=3,
        is_active=True,
    )
    db.add(q)
    await db.flush()
    return q


@pytest_asyncio.fixture
async def inactive_question(db: AsyncSession) -> Question:
    q = Question(
        text_fi="Inactive question",
        question_type="scale5",
        display_order=99,
        is_active=False,
    )
    db.add(q)
    await db.flush()
    return q


@pytest_asyncio.fixture
async def active_questions(
    scale5_question: Question,
    yesno_question: Question,
    text_question: Question,
) -> list[Question]:
    return [scale5_question, yesno_question, text_question]


# ── Fixtures: user helpers ─────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def staff_user(db: AsyncSession) -> StaffUser:
    user = StaffUser(
        email="staff@soite.fi",
        hashed_password=hash_password("StaffPass123!"),
        role="staff",
        is_active=True,
        force_password_change=False,
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession) -> StaffUser:
    user = StaffUser(
        email="admin@soite.fi",
        hashed_password=hash_password("AdminPass123!"),
        role="admin",
        is_active=True,
        force_password_change=False,
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
def staff_token(staff_user: StaffUser) -> str:
    return create_access_token(subject=str(staff_user.id), role="staff")


@pytest_asyncio.fixture
def admin_token(admin_user: StaffUser) -> str:
    return create_access_token(subject=str(admin_user.id), role="admin")


@pytest_asyncio.fixture
def expired_token(staff_user: StaffUser) -> str:
    import jwt as pyjwt
    from app.config import settings
    payload = {
        "sub": str(staff_user.id),
        "role": "staff",
        "exp": datetime.now(UTC) - timedelta(hours=2),
        "iat": datetime.now(UTC) - timedelta(hours=3),
        "jti": str(uuid.uuid4()),
    }
    return pyjwt.encode(payload, settings.secret_key, algorithm="HS256")


@pytest_asyncio.fixture
async def staff_refresh_token(db: AsyncSession, staff_user: StaffUser) -> str:
    raw = "test-refresh-token-" + uuid.uuid4().hex
    db.add(RefreshToken(
        user_id=staff_user.id,
        token_hash=hash_refresh_token(raw),
        expires_at=datetime.now(UTC) + timedelta(days=7),
    ))
    await db.flush()
    return raw


# ── Helper: build valid feedback payload ───────────────────────────────────────

def build_feedback_payload(
    questions: list[Question],
    overrides: dict[str, Any] | None = None,
) -> dict:
    answers = []
    for q in questions:
        if q.question_type == "scale5":
            answers.append({"question_id": str(q.id), "int_value": 4})
        elif q.question_type == "yesno":
            answers.append({"question_id": str(q.id), "int_value": 1})
        elif q.question_type == "text":
            answers.append({"question_id": str(q.id), "text_value": "Good service"})
    payload: dict = {
        "submission_id": str(uuid.uuid4()),
        "answers": answers,
        "submitted_at_local": datetime.now(UTC).isoformat(),
        "app_version": "1.0.0",
    }
    if overrides:
        payload.update(overrides)
    return payload
