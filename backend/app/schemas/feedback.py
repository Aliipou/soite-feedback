"""Pydantic v2 schemas for feedback submission endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AnswerIn(BaseModel):
    """Single answer within a feedback submission."""

    model_config = ConfigDict(strict=True)

    question_id: uuid.UUID
    int_value: int | None = Field(default=None, ge=0, le=5)
    text_value: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def at_least_one_value(self) -> "AnswerIn":
        if self.int_value is None and self.text_value is None:
            msg = "Answer must have either int_value or text_value"
            raise ValueError(msg)
        return self


class FeedbackSubmitIn(BaseModel):
    """Request body for POST /feedback."""

    model_config = ConfigDict(strict=True)

    submission_id: uuid.UUID
    answers: list[AnswerIn] = Field(min_length=1)
    submitted_at_local: datetime
    app_version: str | None = Field(default=None, max_length=16)

    @field_validator("answers")
    @classmethod
    def no_duplicate_questions(cls, v: list[AnswerIn]) -> list[AnswerIn]:
        ids = [a.question_id for a in v]
        if len(ids) != len(set(ids)):
            msg = "Duplicate question_id in answers"
            raise ValueError(msg)
        return v


class FeedbackSubmitOut(BaseModel):
    """Response body for POST /feedback."""

    model_config = ConfigDict(strict=True)

    received: bool = True
