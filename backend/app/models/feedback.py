"""Feedback submission and answer models — no PII stored."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, LargeBinary, SmallInteger, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FeedbackSubmission(Base):
    """One completed survey. Contains zero patient-identifying information."""

    __tablename__ = "feedback_submissions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_submission_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, unique=True, index=True
    )
    device_token: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    question_count: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    app_version: Mapped[str | None] = mapped_column(String(16), nullable=True)

    answers: Mapped[list["FeedbackAnswer"]] = relationship(
        "FeedbackAnswer", back_populates="submission", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<FeedbackSubmission id={self.id} at={self.submitted_at}>"


class FeedbackAnswer(Base):
    """Individual answer within a submission. text_value stored as pgcrypto-encrypted bytes."""

    __tablename__ = "feedback_answers"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("feedback_submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("questions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    int_value: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    text_value: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    submission: Mapped[FeedbackSubmission] = relationship(
        "FeedbackSubmission", back_populates="answers"
    )

    def __repr__(self) -> str:
        return f"<FeedbackAnswer submission={self.submission_id} question={self.question_id}>"
