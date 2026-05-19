"""Feedback submission service — idempotency, validation, pgcrypto encryption."""

import uuid
from datetime import date, datetime

import nh3
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.feedback import FeedbackAnswer, FeedbackSubmission
from app.models.question import Question
from app.schemas.feedback import FeedbackSubmitIn


class FeedbackValidationError(Exception):
    """Raised when submission payload fails business-logic validation."""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


async def _load_active_questions(db: AsyncSession) -> dict[uuid.UUID, Question]:
    """Return map of {id: question} for all active questions."""
    result = await db.execute(
        select(Question).where(Question.is_active.is_(True))
    )
    return {q.id: q for q in result.scalars().all()}


async def create_submission(
    db: AsyncSession,
    payload: FeedbackSubmitIn,
    device_token: uuid.UUID,
) -> FeedbackSubmission:
    """Create a feedback submission with idempotency and full validation.

    Raises FeedbackValidationError on bad input.
    Returns existing submission if client_submission_id already exists (idempotency).
    """
    existing = await db.execute(
        select(FeedbackSubmission).where(
            FeedbackSubmission.client_submission_id == payload.submission_id
        )
    )
    found = existing.scalar_one_or_none()
    if found is not None:
        return found

    active_questions = await _load_active_questions(db)

    # Every non-text active question must be answered
    answered_ids = {a.question_id for a in payload.answers}
    for q_id, q in active_questions.items():
        if q.question_type != "text" and q_id not in answered_ids:
            raise FeedbackValidationError(
                f"Missing answer for required question {q_id}", field="answers"
            )

    # Validate each answer against the question it references
    for answer in payload.answers:
        q = active_questions.get(answer.question_id)
        if q is None:
            raise FeedbackValidationError(
                f"Question {answer.question_id} not found or inactive",
                field="answers",
            )
        if q.question_type == "scale5":
            if answer.int_value is None or not (1 <= answer.int_value <= 5):
                raise FeedbackValidationError(
                    "scale5 answer requires int_value 1–5",
                    field=f"answers[question_id={answer.question_id}].int_value",
                )
        elif q.question_type == "face4":
            if answer.int_value is None or not (1 <= answer.int_value <= 4):
                raise FeedbackValidationError(
                    "face4 answer requires int_value 1–4",
                    field=f"answers[question_id={answer.question_id}].int_value",
                )
        elif q.question_type == "yesno":
            if answer.int_value not in (0, 1):
                raise FeedbackValidationError(
                    "yesno answer requires int_value 0 or 1",
                    field=f"answers[question_id={answer.question_id}].int_value",
                )

    submission = FeedbackSubmission(
        client_submission_id=payload.submission_id,
        device_token=device_token,
        question_count=len(active_questions),
        app_version=payload.app_version,
    )
    db.add(submission)
    await db.flush()

    for answer in payload.answers:
        q = active_questions[answer.question_id]
        fa = FeedbackAnswer(
            submission_id=submission.id,
            question_id=answer.question_id,
            int_value=answer.int_value,
        )
        if q.question_type == "text" and answer.text_value:
            cleaned = nh3.clean(answer.text_value)[:500]
            # pgp_sym_encrypt via raw SQL — key from environment, never hardcoded
            result = await db.execute(
                text("SELECT pgp_sym_encrypt(:plaintext, :key)"),
                {"plaintext": cleaned, "key": settings.pgcrypto_key},
            )
            fa.text_value = result.scalar_one()
        db.add(fa)

    return submission


async def get_submission_count_in_range(
    db: AsyncSession,
    from_date: date,
    to_date: date,
) -> int:
    """Return total submission count within date range."""
    result = await db.execute(
        select(func.count(FeedbackSubmission.id)).where(
            func.date(FeedbackSubmission.submitted_at) >= from_date,
            func.date(FeedbackSubmission.submitted_at) <= to_date,
        )
    )
    return result.scalar_one()


async def get_answer_stats(
    db: AsyncSession,
    question_id: uuid.UUID,
    from_date: date,
    to_date: date,
) -> dict[str, int]:
    """Return value distribution for a scale5 or yesno question in date range."""
    result = await db.execute(
        select(FeedbackAnswer.int_value, func.count(FeedbackAnswer.id))
        .join(FeedbackSubmission, FeedbackAnswer.submission_id == FeedbackSubmission.id)
        .where(
            FeedbackAnswer.question_id == question_id,
            FeedbackAnswer.int_value.isnot(None),
            func.date(FeedbackSubmission.submitted_at) >= from_date,
            func.date(FeedbackSubmission.submitted_at) <= to_date,
        )
        .group_by(FeedbackAnswer.int_value)
    )
    return {str(row[0]): row[1] for row in result.all()}


async def get_freetext_answers(
    db: AsyncSession,
    question_id: uuid.UUID,
    page: int,
    per_page: int,
) -> tuple[int, list[str]]:
    """Return paginated plaintext free-text answers, decrypted server-side.

    Returns (total_count, list_of_texts).
    """
    count_result = await db.execute(
        select(func.count(FeedbackAnswer.id)).where(
            FeedbackAnswer.question_id == question_id,
            FeedbackAnswer.text_value.isnot(None),
        )
    )
    total = count_result.scalar_one()

    if total == 0:
        return 0, []

    offset = (page - 1) * per_page
    rows = await db.execute(
        text(
            "SELECT pgp_sym_decrypt(fa.text_value, :key) "
            "FROM feedback_answers fa "
            "WHERE fa.question_id = :qid AND fa.text_value IS NOT NULL "
            "ORDER BY fa.answered_at DESC "
            "LIMIT :limit OFFSET :offset"
        ),
        {
            "key": settings.pgcrypto_key,
            "qid": str(question_id),
            "limit": per_page,
            "offset": offset,
        },
    )
    texts = [str(row[0]) for row in rows.all()]
    return total, texts


async def purge_old_submissions(db: AsyncSession, cutoff: datetime) -> int:
    """Delete submissions older than cutoff. Returns number of rows deleted."""
    result = await db.execute(
        select(FeedbackSubmission).where(FeedbackSubmission.submitted_at < cutoff)
    )
    old = result.scalars().all()
    count = len(old)
    for sub in old:
        await db.delete(sub)
    return count
