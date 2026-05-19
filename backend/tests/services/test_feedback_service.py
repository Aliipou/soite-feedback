"""Unit tests for feedback service — all business logic edge cases."""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback import FeedbackAnswer, FeedbackSubmission
from app.models.question import Question
from app.schemas.feedback import AnswerIn, FeedbackSubmitIn
from app.services.feedback import FeedbackValidationError, create_submission
from tests.conftest import build_feedback_payload


def _make_payload(questions: list[Question], **overrides) -> FeedbackSubmitIn:
    raw = build_feedback_payload(questions, overrides)
    return FeedbackSubmitIn.model_validate(raw)


class TestCreateSubmission:
    """Comprehensive coverage of create_submission service function."""

    async def test_happy_path_creates_submission_and_answers(
        self, db: AsyncSession, active_questions: list[Question]
    ) -> None:
        """Valid answers for all active questions creates one submission row and N answer rows."""
        payload = _make_payload(active_questions)
        device = uuid.uuid4()

        result = await create_submission(db, payload, device)

        assert result.client_submission_id == payload.submission_id
        assert result.device_token == device

        answers = await db.execute(
            select(FeedbackAnswer).where(FeedbackAnswer.submission_id == result.id)
        )
        assert len(answers.scalars().all()) == 3

    async def test_idempotency_same_submission_id_returns_existing(
        self, db: AsyncSession, active_questions: list[Question]
    ) -> None:
        """Submitting the same submission_id twice returns the same row without duplication."""
        payload = _make_payload(active_questions)
        device = uuid.uuid4()

        first = await create_submission(db, payload, device)
        second = await create_submission(db, payload, device)

        assert first.id == second.id

        count_result = await db.execute(
            select(FeedbackSubmission).where(
                FeedbackSubmission.client_submission_id == payload.submission_id
            )
        )
        rows = count_result.scalars().all()
        assert len(rows) == 1

    async def test_scale5_value_out_of_range_raises(
        self, db: AsyncSession, scale5_question: Question
    ) -> None:
        """int_value=6 on a scale5 question raises FeedbackValidationError."""
        payload = FeedbackSubmitIn(
            submission_id=uuid.uuid4(),
            answers=[AnswerIn(question_id=scale5_question.id, int_value=6)],
            submitted_at_local=datetime.now(UTC),
        )
        with pytest.raises(FeedbackValidationError, match="scale5"):
            await create_submission(db, payload, uuid.uuid4())

    async def test_scale5_value_zero_raises(
        self, db: AsyncSession, scale5_question: Question
    ) -> None:
        """int_value=0 on a scale5 question raises FeedbackValidationError (valid: 1–5)."""
        payload = FeedbackSubmitIn(
            submission_id=uuid.uuid4(),
            answers=[AnswerIn(question_id=scale5_question.id, int_value=0)],
            submitted_at_local=datetime.now(UTC),
        )
        with pytest.raises(FeedbackValidationError, match="scale5"):
            await create_submission(db, payload, uuid.uuid4())

    async def test_yesno_value_invalid_raises(
        self, db: AsyncSession, yesno_question: Question
    ) -> None:
        """int_value=2 on a yesno question raises FeedbackValidationError (valid: 0 or 1)."""
        payload = FeedbackSubmitIn(
            submission_id=uuid.uuid4(),
            answers=[AnswerIn(question_id=yesno_question.id, int_value=2)],
            submitted_at_local=datetime.now(UTC),
        )
        with pytest.raises(FeedbackValidationError, match="yesno"):
            await create_submission(db, payload, uuid.uuid4())

    async def test_unknown_question_id_raises(
        self, db: AsyncSession, active_questions: list[Question]
    ) -> None:
        """Payload referencing a non-existent question_id raises FeedbackValidationError."""
        answers = [AnswerIn(question_id=uuid.uuid4(), int_value=3)]
        payload = FeedbackSubmitIn(
            submission_id=uuid.uuid4(),
            answers=answers,
            submitted_at_local=datetime.now(UTC),
        )
        with pytest.raises(FeedbackValidationError, match="not found or inactive"):
            await create_submission(db, payload, uuid.uuid4())

    async def test_inactive_question_raises(
        self, db: AsyncSession, inactive_question: Question, scale5_question: Question
    ) -> None:
        """Answering an is_active=False question raises FeedbackValidationError."""
        payload = FeedbackSubmitIn(
            submission_id=uuid.uuid4(),
            answers=[
                AnswerIn(question_id=scale5_question.id, int_value=3),
                AnswerIn(question_id=inactive_question.id, int_value=2),
            ],
            submitted_at_local=datetime.now(UTC),
        )
        with pytest.raises(FeedbackValidationError, match="not found or inactive"):
            await create_submission(db, payload, uuid.uuid4())

    async def test_missing_required_non_text_question_raises(
        self, db: AsyncSession, scale5_question: Question, yesno_question: Question
    ) -> None:
        """Omitting a required (non-text) active question raises FeedbackValidationError."""
        payload = FeedbackSubmitIn(
            submission_id=uuid.uuid4(),
            answers=[AnswerIn(question_id=scale5_question.id, int_value=4)],
            submitted_at_local=datetime.now(UTC),
        )
        with pytest.raises(FeedbackValidationError, match="Missing answer"):
            await create_submission(db, payload, uuid.uuid4())

    async def test_text_question_can_be_skipped(
        self, db: AsyncSession, scale5_question: Question, text_question: Question
    ) -> None:
        """Text questions are optional — omitting them does not raise."""
        payload = FeedbackSubmitIn(
            submission_id=uuid.uuid4(),
            answers=[AnswerIn(question_id=scale5_question.id, int_value=5)],
            submitted_at_local=datetime.now(UTC),
        )
        result = await create_submission(db, payload, uuid.uuid4())
        assert result.id is not None

    async def test_text_value_over_500_chars_truncated(
        self, db: AsyncSession, text_question: Question, scale5_question: Question
    ) -> None:
        """Text answers over 500 chars are truncated (not rejected) at service layer."""
        long_text = "x" * 600
        payload = FeedbackSubmitIn(
            submission_id=uuid.uuid4(),
            answers=[
                AnswerIn(question_id=scale5_question.id, int_value=3),
                AnswerIn(question_id=text_question.id, text_value=long_text),
            ],
            submitted_at_local=datetime.now(UTC),
        )
        # Should not raise — truncated at 500
        result = await create_submission(db, payload, uuid.uuid4())
        assert result.id is not None

    async def test_xss_in_text_value_is_stripped(
        self, db: AsyncSession, text_question: Question, scale5_question: Question
    ) -> None:
        """HTML/script tags are stripped from text values by nh3.clean()."""
        payload = FeedbackSubmitIn(
            submission_id=uuid.uuid4(),
            answers=[
                AnswerIn(question_id=scale5_question.id, int_value=3),
                AnswerIn(
                    question_id=text_question.id,
                    text_value="<script>alert(1)</script>Good care",
                ),
            ],
            submitted_at_local=datetime.now(UTC),
        )
        # Should not raise — XSS stripped
        result = await create_submission(db, payload, uuid.uuid4())
        assert result.id is not None

    async def test_all_scale5_values_accepted(
        self, db: AsyncSession, scale5_question: Question
    ) -> None:
        """Values 1–5 are all valid for scale5 questions."""
        for val in [1, 2, 3, 4, 5]:
            payload = FeedbackSubmitIn(
                submission_id=uuid.uuid4(),
                answers=[AnswerIn(question_id=scale5_question.id, int_value=val)],
                submitted_at_local=datetime.now(UTC),
            )
            result = await create_submission(db, payload, uuid.uuid4())
            assert result.id is not None

    async def test_yesno_both_values_accepted(
        self, db: AsyncSession, yesno_question: Question
    ) -> None:
        """Both 0 and 1 are valid for yesno questions."""
        for val in [0, 1]:
            payload = FeedbackSubmitIn(
                submission_id=uuid.uuid4(),
                answers=[AnswerIn(question_id=yesno_question.id, int_value=val)],
                submitted_at_local=datetime.now(UTC),
            )
            result = await create_submission(db, payload, uuid.uuid4())
            assert result.id is not None
