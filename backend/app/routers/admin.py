"""Admin endpoints — JWT required, role: admin."""

import csv
import io
import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import CreateUserIn, UpdateUserIn, UserOut
from app.schemas.question import AdminQuestionOut, CreateQuestionIn, UpdateQuestionIn
from app.security.dependencies import AdminPayload
from app.services import question as question_svc
from app.services import user as user_svc
from app.models.feedback import FeedbackAnswer, FeedbackSubmission

router = APIRouter(prefix="/admin")


# ── Questions ──────────────────────────────────────────────────────────────────

@router.get("/questions", response_model=list[AdminQuestionOut])
async def list_questions(
    payload: AdminPayload,
    db: AsyncSession = Depends(get_db),
) -> list[AdminQuestionOut]:
    """All questions (active + inactive) for admin panel."""
    questions = await question_svc.get_all_questions(db)
    return [AdminQuestionOut.model_validate(q) for q in questions]


@router.post("/questions", response_model=AdminQuestionOut, status_code=status.HTTP_201_CREATED)
async def create_question(
    body: CreateQuestionIn,
    payload: AdminPayload,
    db: AsyncSession = Depends(get_db),
) -> AdminQuestionOut:
    """Create a new survey question."""
    actor_id = uuid.UUID(payload["sub"])
    q = await question_svc.create_question(
        db,
        text_fi=body.text_fi,
        text_sv=body.text_sv,
        question_type=body.type,
        display_order=body.order,
        actor_id=actor_id,
    )
    return AdminQuestionOut.model_validate(q)


@router.patch("/questions/{question_id}", response_model=AdminQuestionOut)
async def update_question(
    question_id: uuid.UUID,
    body: UpdateQuestionIn,
    payload: AdminPayload,
    db: AsyncSession = Depends(get_db),
) -> AdminQuestionOut:
    """Update question fields. Logs change to audit_log."""
    q = await question_svc.get_question_by_id(db, question_id)
    if q is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Question not found"},
        )
    actor_id = uuid.UUID(payload["sub"])
    updated = await question_svc.update_question(
        db, q, actor_id,
        text_fi=body.text_fi,
        text_sv=body.text_sv,
        display_order=body.order,
        is_active=body.is_active,
    )
    return AdminQuestionOut.model_validate(updated)


# ── Users ──────────────────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UserOut])
async def list_users(
    payload: AdminPayload,
    db: AsyncSession = Depends(get_db),
) -> list[UserOut]:
    """List all staff accounts."""
    users = await user_svc.get_all_users(db)
    return [UserOut.model_validate(u) for u in users]


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: CreateUserIn,
    payload: AdminPayload,
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """Create a staff account. Password hashed with bcrypt(12)."""
    actor_id = uuid.UUID(payload["sub"])
    try:
        user = await user_svc.create_user(db, body.email, body.password, body.role, actor_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "VALIDATION_ERROR", "message": "Email already registered"},
        )
    return UserOut.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    body: UpdateUserIn,
    payload: AdminPayload,
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """Deactivate user or change role. Logs to audit_log."""
    user = await user_svc.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "User not found"},
        )
    actor_id = uuid.UUID(payload["sub"])
    updated = await user_svc.update_user(db, user, actor_id, body.is_active, body.role)
    return UserOut.model_validate(updated)


# ── Export ─────────────────────────────────────────────────────────────────────

@router.get("/export")
async def export_csv(
    payload: AdminPayload,
    from_date: str = Query(
        default_factory=lambda: (date.today() - timedelta(days=30)).isoformat(),
        alias="from",
    ),
    to_date: str = Query(default_factory=lambda: date.today().isoformat(), alias="to"),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Export anonymised CSV of all answers in date range."""
    try:
        fd = date.fromisoformat(from_date)
        td = date.fromisoformat(to_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_ERROR", "message": "Invalid date format"},
        )

    rows = await db.execute(
        select(
            FeedbackSubmission.submitted_at,
            FeedbackAnswer.question_id,
            FeedbackAnswer.int_value,
        )
        .join(FeedbackAnswer, FeedbackAnswer.submission_id == FeedbackSubmission.id)
        .where(
            FeedbackAnswer.int_value.isnot(None),
            FeedbackSubmission.submitted_at >= fd.isoformat(),
            FeedbackSubmission.submitted_at <= td.isoformat() + "T23:59:59",
        )
        .order_by(FeedbackSubmission.submitted_at)
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["submitted_at", "question_id", "value"])
    for row in rows.all():
        writer.writerow([row[0].isoformat(), str(row[1]), row[2]])

    output.seek(0)
    filename = f"soite-palaute-{from_date}--{to_date}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
