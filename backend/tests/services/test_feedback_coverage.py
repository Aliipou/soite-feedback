"""Coverage tests for feedback service — stats, purge, face4 validation, freetext."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question
from app.schemas.feedback import AnswerIn, FeedbackSubmitIn
from app.services.feedback import (
    FeedbackValidationError,
    create_submission,
    get_answer_stats,
    get_freetext_answers,
    get_submission_count_in_range,
    purge_old_submissions,
)
from tests.conftest import _IS_PG

pytestmark = pytest.mark.asyncio


# ── helpers ───────────────────────────────────────────────────────────────────

async def _submit(db: AsyncSession, question: Question, int_val: int) -> None:
    payload = FeedbackSubmitIn(
        submission_id=uuid.uuid4(),
        answers=[AnswerIn(question_id=question.id, int_value=int_val)],
        submitted_at_local=datetime.now(UTC),
    )
    await create_submission(db, payload, uuid.uuid4())


# ── face4 validation ─────────────────────────────────────────────────────────


class TestFace4Validation:
    async def test_value_1_accepted(self, db: AsyncSession, face4_question: Question) -> None:
        await _submit(db, face4_question, 1)

    async def test_value_2_accepted(self, db: AsyncSession, face4_question: Question) -> None:
        await _submit(db, face4_question, 2)

    async def test_value_3_accepted(self, db: AsyncSession, face4_question: Question) -> None:
        await _submit(db, face4_question, 3)

    async def test_value_4_accepted(self, db: AsyncSession, face4_question: Question) -> None:
        await _submit(db, face4_question, 4)

    async def test_value_0_raises(self, db: AsyncSession, face4_question: Question) -> None:
        payload = FeedbackSubmitIn(
            submission_id=uuid.uuid4(),
            answers=[AnswerIn(question_id=face4_question.id, int_value=0)],
            submitted_at_local=datetime.now(UTC),
        )
        with pytest.raises(FeedbackValidationError, match="face4"):
            await create_submission(db, payload, uuid.uuid4())

    async def test_value_5_raises(self, db: AsyncSession, face4_question: Question) -> None:
        payload = FeedbackSubmitIn(
            submission_id=uuid.uuid4(),
            answers=[AnswerIn(question_id=face4_question.id, int_value=5)],
            submitted_at_local=datetime.now(UTC),
        )
        with pytest.raises(FeedbackValidationError, match="face4"):
            await create_submission(db, payload, uuid.uuid4())

    async def test_none_int_value_raises(self, db: AsyncSession, face4_question: Question) -> None:
        payload = FeedbackSubmitIn(
            submission_id=uuid.uuid4(),
            answers=[AnswerIn(question_id=face4_question.id, int_value=None)],
            submitted_at_local=datetime.now(UTC),
        )
        with pytest.raises(FeedbackValidationError, match="face4"):
            await create_submission(db, payload, uuid.uuid4())

    async def test_missing_face4_raises(
        self, db: AsyncSession, face4_question: Question, scale5_question: Question
    ) -> None:
        # Only answer scale5; face4 is required (non-text) → Missing answer error
        payload = FeedbackSubmitIn(
            submission_id=uuid.uuid4(),
            answers=[AnswerIn(question_id=scale5_question.id, int_value=4)],
            submitted_at_local=datetime.now(UTC),
        )
        with pytest.raises(FeedbackValidationError, match="Missing answer"):
            await create_submission(db, payload, uuid.uuid4())

    async def test_error_has_field_attribute(
        self, db: AsyncSession, face4_question: Question
    ) -> None:
        payload = FeedbackSubmitIn(
            submission_id=uuid.uuid4(),
            answers=[AnswerIn(question_id=face4_question.id, int_value=0)],
            submitted_at_local=datetime.now(UTC),
        )
        with pytest.raises(FeedbackValidationError) as exc_info:
            await create_submission(db, payload, uuid.uuid4())
        assert exc_info.value.field is not None


# ── FeedbackValidationError class ────────────────────────────────────────────


class TestFeedbackValidationError:
    def test_message_accessible(self) -> None:
        err = FeedbackValidationError("bad input", field="answers")
        assert str(err) == "bad input"
        assert err.field == "answers"

    def test_field_defaults_to_none(self) -> None:
        err = FeedbackValidationError("oops")
        assert err.field is None


# ── submission count ─────────────────────────────────────────────────────────


class TestSubmissionCountInRange:
    async def test_returns_correct_count(
        self, db: AsyncSession, scale5_question: Question
    ) -> None:
        today = datetime.now(UTC).date()
        for _ in range(3):
            await _submit(db, scale5_question, 4)
        count = await get_submission_count_in_range(db, today, today)
        assert count == 3

    async def test_empty_returns_zero(self, db: AsyncSession) -> None:
        yesterday = (datetime.now(UTC) - timedelta(days=1)).date()
        count = await get_submission_count_in_range(db, yesterday, yesterday)
        assert count == 0

    async def test_date_range_excludes_future(self, db: AsyncSession, scale5_question: Question) -> None:
        today = datetime.now(UTC).date()
        await _submit(db, scale5_question, 3)
        past = today - timedelta(days=30)
        two_days_ago = today - timedelta(days=2)
        # Range excludes today → 0
        count = await get_submission_count_in_range(db, past, two_days_ago)
        assert count == 0


# ── answer stats ─────────────────────────────────────────────────────────────


class TestGetAnswerStats:
    async def test_returns_distribution(
        self, db: AsyncSession, scale5_question: Question
    ) -> None:
        today = datetime.now(UTC).date()
        for val in [3, 3, 4, 5]:
            await _submit(db, scale5_question, val)
        stats = await get_answer_stats(db, scale5_question.id, today, today)
        assert stats["3"] == 2
        assert stats["4"] == 1
        assert stats["5"] == 1
        assert "1" not in stats

    async def test_no_answers_returns_empty(
        self, db: AsyncSession, scale5_question: Question
    ) -> None:
        today = datetime.now(UTC).date()
        stats = await get_answer_stats(db, scale5_question.id, today, today)
        assert stats == {}

    async def test_unknown_question_returns_empty(self, db: AsyncSession) -> None:
        today = datetime.now(UTC).date()
        stats = await get_answer_stats(db, uuid.uuid4(), today, today)
        assert stats == {}

    async def test_face4_distribution_correct(
        self, db: AsyncSession, face4_question: Question
    ) -> None:
        today = datetime.now(UTC).date()
        for val in [1, 2, 4, 4]:
            await _submit(db, face4_question, val)
        stats = await get_answer_stats(db, face4_question.id, today, today)
        assert stats["1"] == 1
        assert stats["2"] == 1
        assert stats["4"] == 2
        assert "3" not in stats


# ── purge old submissions ─────────────────────────────────────────────────────


class TestPurgeOldSubmissions:
    async def test_deletes_old_and_returns_count(
        self, db: AsyncSession, scale5_question: Question
    ) -> None:
        payload = FeedbackSubmitIn(
            submission_id=uuid.uuid4(),
            answers=[AnswerIn(question_id=scale5_question.id, int_value=3)],
            submitted_at_local=datetime.now(UTC),
        )
        sub = await create_submission(db, payload, uuid.uuid4())
        sub.submitted_at = datetime.now(UTC) - timedelta(days=400)
        await db.flush()

        deleted = await purge_old_submissions(db, datetime.now(UTC) - timedelta(days=30))
        assert deleted == 1

    async def test_keeps_recent(self, db: AsyncSession, scale5_question: Question) -> None:
        await _submit(db, scale5_question, 3)
        deleted = await purge_old_submissions(db, datetime.now(UTC) - timedelta(days=30))
        assert deleted == 0

    async def test_empty_table_returns_zero(self, db: AsyncSession) -> None:
        deleted = await purge_old_submissions(db, datetime.now(UTC) - timedelta(days=30))
        assert deleted == 0

    async def test_only_deletes_before_cutoff(
        self, db: AsyncSession, scale5_question: Question
    ) -> None:
        payload_old = FeedbackSubmitIn(
            submission_id=uuid.uuid4(),
            answers=[AnswerIn(question_id=scale5_question.id, int_value=3)],
            submitted_at_local=datetime.now(UTC),
        )
        sub_old = await create_submission(db, payload_old, uuid.uuid4())
        sub_old.submitted_at = datetime.now(UTC) - timedelta(days=400)
        await db.flush()

        # Recent submission — should survive
        await _submit(db, scale5_question, 5)

        deleted = await purge_old_submissions(db, datetime.now(UTC) - timedelta(days=30))
        assert deleted == 1  # only old one deleted


# ── freetext answers (PostgreSQL only) ────────────────────────────────────────


@pytest.mark.skipif(not _IS_PG, reason="requires PostgreSQL pgcrypto")
class TestGetFreetextAnswers:
    async def test_returns_decrypted_text(
        self, db: AsyncSession, scale5_question: Question, text_question: Question
    ) -> None:
        payload = FeedbackSubmitIn(
            submission_id=uuid.uuid4(),
            answers=[
                AnswerIn(question_id=scale5_question.id, int_value=4),
                AnswerIn(question_id=text_question.id, text_value="Great service!"),
            ],
            submitted_at_local=datetime.now(UTC),
        )
        await create_submission(db, payload, uuid.uuid4())
        total, texts = await get_freetext_answers(db, text_question.id, page=1, per_page=10)
        assert total == 1
        assert texts[0] == "Great service!"

    async def test_empty_returns_zero_total(
        self, db: AsyncSession, text_question: Question
    ) -> None:
        total, texts = await get_freetext_answers(db, text_question.id, page=1, per_page=10)
        assert total == 0
        assert texts == []

    async def test_page_beyond_total_returns_empty_list(
        self, db: AsyncSession, text_question: Question
    ) -> None:
        total, texts = await get_freetext_answers(db, text_question.id, page=99, per_page=10)
        assert total == 0
        assert texts == []

    async def test_pagination_splits_correctly(
        self, db: AsyncSession, scale5_question: Question, text_question: Question
    ) -> None:
        for i in range(5):
            payload = FeedbackSubmitIn(
                submission_id=uuid.uuid4(),
                answers=[
                    AnswerIn(question_id=scale5_question.id, int_value=4),
                    AnswerIn(question_id=text_question.id, text_value=f"Answer {i}"),
                ],
                submitted_at_local=datetime.now(UTC),
            )
            await create_submission(db, payload, uuid.uuid4())

        total, page1 = await get_freetext_answers(db, text_question.id, page=1, per_page=2)
        assert total == 5
        assert len(page1) == 2

        _, page2 = await get_freetext_answers(db, text_question.id, page=2, per_page=2)
        assert len(page2) == 2

        _, page3 = await get_freetext_answers(db, text_question.id, page=3, per_page=2)
        assert len(page3) == 1

    async def test_unknown_question_returns_zero(self, db: AsyncSession) -> None:
        total, texts = await get_freetext_answers(db, uuid.uuid4(), page=1, per_page=10)
        assert total == 0
        assert texts == []
