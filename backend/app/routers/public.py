"""Public endpoints — no authentication required."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.feedback import FeedbackSubmitIn, FeedbackSubmitOut
from app.schemas.question import QuestionOut, SurveyQuestionsOut
from app.services import feedback as feedback_svc
from app.services import question as question_svc

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def _get_device_token(x_device_token: str | None = Header(default=None)) -> uuid.UUID:
    """Extract and validate X-Device-Token header."""
    if x_device_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_ERROR", "message": "X-Device-Token header required"},
        )
    try:
        return uuid.UUID(x_device_token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_ERROR", "message": "X-Device-Token must be a valid UUID"},
        )


@router.get("/survey/questions", response_model=SurveyQuestionsOut)
async def get_survey_questions(db: AsyncSession = Depends(get_db)) -> SurveyQuestionsOut:
    """Return active questions in display order. Cached 5 min by nginx/CDN."""
    questions = await question_svc.get_active_questions(db)
    version = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return SurveyQuestionsOut(
        questions=[QuestionOut.model_validate(q) for q in questions],
        version=version,
    )


@router.post(
    "/feedback",
    response_model=FeedbackSubmitOut,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("3/hour")
async def submit_feedback(
    request: Request,
    payload: FeedbackSubmitIn,
    device_token: uuid.UUID = Depends(_get_device_token),
    db: AsyncSession = Depends(get_db),
) -> FeedbackSubmitOut:
    """Submit a completed survey. Rate limited: 3/hour per IP (device_token used for idempotency).

    No CSRF protection needed: JSON-only, no auth session to hijack.
    """
    try:
        await feedback_svc.create_submission(db, payload, device_token)
    except feedback_svc.FeedbackValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "VALIDATION_ERROR",
                "message": str(exc),
                "fields": {exc.field: str(exc)} if exc.field else {},
            },
        ) from exc
    return FeedbackSubmitOut(received=True)


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict:
    """Health check — verifies DB connectivity. Returns 200 or 503."""
    try:
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "INTERNAL_ERROR", "message": "Database unavailable"},
        ) from exc
    return {"status": "ok"}
