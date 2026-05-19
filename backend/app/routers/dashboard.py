"""Staff dashboard endpoints — JWT required, role: staff or admin."""

import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.feedback import FeedbackAnswer, FeedbackSubmission
from app.models.question import Question
from app.schemas.dashboard import (
    DashboardSummaryOut,
    FreetextItemOut,
    FreetextPageOut,
    PeriodOut,
    QuestionSummaryOut,
)
from app.security.dependencies import AuthPayload
from app.services import feedback as feedback_svc
from app.services import question as question_svc

router = APIRouter(prefix="/dashboard")


def _default_from() -> str:
    return (date.today() - timedelta(days=30)).isoformat()


def _default_to() -> str:
    return date.today().isoformat()


@router.get("/summary", response_model=DashboardSummaryOut)
async def get_summary(
    payload: AuthPayload,
    from_date: str = Query(default_factory=_default_from, alias="from"),
    to_date: str = Query(default_factory=_default_to, alias="to"),
    db: AsyncSession = Depends(get_db),
) -> DashboardSummaryOut:
    """Aggregate statistics for all questions in the given date range."""
    try:
        fd = date.fromisoformat(from_date)
        td = date.fromisoformat(to_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_ERROR", "message": "Invalid date format — use YYYY-MM-DD"},
        )

    total = await feedback_svc.get_submission_count_in_range(db, fd, td)
    all_questions = await question_svc.get_active_questions(db)

    by_question: list[QuestionSummaryOut] = []
    for q in all_questions:
        if q.question_type in ("scale5", "yesno"):
            counts = await feedback_svc.get_answer_stats(db, q.id, fd, td)
            mean: float | None = None
            if counts and q.question_type == "scale5":
                total_answers = sum(counts.values())
                if total_answers > 0:
                    mean = sum(int(k) * v for k, v in counts.items()) / total_answers
                    mean = round(mean, 2)
            by_question.append(QuestionSummaryOut(
                question_id=str(q.id),
                text_fi=q.text_fi,
                type=q.question_type,
                counts=counts,
                mean=mean,
            ))
        else:
            # Text question — count responses with non-null encrypted text
            text_count_result = await db.execute(
                select(func.count(FeedbackAnswer.id)).where(
                    FeedbackAnswer.question_id == q.id,
                    FeedbackAnswer.text_value.isnot(None),
                )
            )
            text_total: int = text_count_result.scalar_one()
            by_question.append(QuestionSummaryOut(
                question_id=str(q.id),
                text_fi=q.text_fi,
                type=q.question_type,
                total=text_total,
            ))

    return DashboardSummaryOut(
        period=PeriodOut(from_date=from_date, to_date=to_date),
        total_submissions=total,
        by_question=by_question,
    )


@router.get("/freetext", response_model=FreetextPageOut)
async def get_freetext(
    payload: AuthPayload,
    question_id: uuid.UUID = Query(...),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> FreetextPageOut:
    """Paginated free-text answers. No metadata shown — privacy by design."""
    q = await question_svc.get_question_by_id(db, question_id)
    if q is None or q.question_type != "text":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Text question not found"},
        )

    total, texts = await feedback_svc.get_freetext_answers(db, question_id, page, per_page)
    return FreetextPageOut(
        total=total,
        page=page,
        items=[FreetextItemOut(text=t) for t in texts],
    )
