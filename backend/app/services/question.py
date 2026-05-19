"""Question service — CRUD with audit logging."""

import uuid
from datetime import UTC, datetime

import nh3
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question
from app.models.user import AuditLog


async def get_active_questions(db: AsyncSession) -> list[Question]:
    """Return active questions ordered by display_order."""
    result = await db.execute(
        select(Question)
        .where(Question.is_active.is_(True))
        .order_by(Question.display_order)
    )
    return list(result.scalars().all())


async def get_all_questions(db: AsyncSession) -> list[Question]:
    """Return all questions (active + inactive) for admin panel."""
    result = await db.execute(select(Question).order_by(Question.display_order))
    return list(result.scalars().all())


async def get_question_by_id(db: AsyncSession, question_id: uuid.UUID) -> Question | None:
    """Return a single question by ID, or None."""
    result = await db.execute(select(Question).where(Question.id == question_id))
    return result.scalar_one_or_none()


async def create_question(
    db: AsyncSession,
    text_fi: str,
    text_en: str | None,
    question_type: str,
    display_order: int,
    actor_id: uuid.UUID,
) -> Question:
    """Create a question and write an audit log entry."""
    q = Question(
        text_fi=nh3.clean(text_fi),
        text_en=nh3.clean(text_en) if text_en else None,
        question_type=question_type,
        display_order=display_order,
        is_active=True,
    )
    db.add(q)
    await db.flush()

    db.add(AuditLog(
        actor_id=actor_id,
        action="question.create",
        target_id=q.id,
        after_json={
            "text_fi": q.text_fi,
            "question_type": q.question_type,
            "display_order": q.display_order,
        },
    ))
    return q


async def update_question(
    db: AsyncSession,
    question: Question,
    actor_id: uuid.UUID,
    text_fi: str | None = None,
    text_en: str | None = None,
    display_order: int | None = None,
    is_active: bool | None = None,
) -> Question:
    """Update allowed fields and write audit log."""
    before = {
        "text_fi": question.text_fi,
        "text_en": question.text_en,
        "display_order": question.display_order,
        "is_active": question.is_active,
    }

    if text_fi is not None:
        question.text_fi = nh3.clean(text_fi)
    if text_en is not None:
        question.text_en = nh3.clean(text_en)
    if display_order is not None:
        question.display_order = display_order
    if is_active is not None:
        question.is_active = is_active
    question.updated_at = datetime.now(UTC)

    await db.flush()

    db.add(AuditLog(
        actor_id=actor_id,
        action="question.update",
        target_id=question.id,
        before_json=before,
        after_json={
            "text_fi": question.text_fi,
            "text_en": question.text_en,
            "display_order": question.display_order,
            "is_active": question.is_active,
        },
    ))
    return question
