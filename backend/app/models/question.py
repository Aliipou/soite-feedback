"""Question model — survey questions managed by admin."""

import uuid
from datetime import datetime
from typing import Literal

from sqlalchemy import Boolean, DateTime, SmallInteger, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

QuestionType = Literal["scale5", "yesno", "text", "face4"]


class Question(Base):
    """Survey question. Soft-deleted via is_active=False; never hard-deleted."""

    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    text_fi: Mapped[str] = mapped_column(Text, nullable=False)
    text_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_sv: Mapped[str | None] = mapped_column(Text, nullable=True)
    question_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="scale5 | yesno | text | face4",
    )
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Question id={self.id} type={self.question_type} active={self.is_active}>"
