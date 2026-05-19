"""Pydantic v2 schemas for question management."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

QuestionType = Literal["scale5", "yesno", "text"]


class QuestionOut(BaseModel):
    """Question as returned to the kiosk (active questions only)."""

    model_config = ConfigDict(strict=True, from_attributes=True)

    id: uuid.UUID
    text_fi: str
    text_en: str | None = None
    type: str = Field(alias="question_type")
    order: int = Field(alias="display_order")

    model_config = ConfigDict(strict=False, from_attributes=True, populate_by_name=True)


class SurveyQuestionsOut(BaseModel):
    """Response for GET /survey/questions."""

    model_config = ConfigDict(strict=True)

    questions: list[QuestionOut]
    version: str


class AdminQuestionOut(BaseModel):
    """Full question representation for admin panel (includes inactive)."""

    model_config = ConfigDict(strict=False, from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    text_fi: str
    text_en: str | None = None
    type: str = Field(alias="question_type")
    order: int = Field(alias="display_order")
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CreateQuestionIn(BaseModel):
    """Request body for POST /admin/questions."""

    model_config = ConfigDict(strict=True)

    text_fi: str = Field(min_length=1, max_length=500)
    text_en: str | None = Field(default=None, max_length=500)
    type: QuestionType
    order: int = Field(ge=0, le=1000)


class UpdateQuestionIn(BaseModel):
    """Request body for PATCH /admin/questions/{id} — all fields optional."""

    model_config = ConfigDict(strict=True)

    text_fi: str | None = Field(default=None, min_length=1, max_length=500)
    text_en: str | None = Field(default=None, max_length=500)
    order: int | None = Field(default=None, ge=0, le=1000)
    is_active: bool | None = None
