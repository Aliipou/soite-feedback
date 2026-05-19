"""Pydantic v2 schemas for staff dashboard endpoints."""

from pydantic import BaseModel, ConfigDict


class PeriodOut(BaseModel):
    model_config = ConfigDict(strict=True)

    from_date: str
    to_date: str


class QuestionSummaryOut(BaseModel):
    model_config = ConfigDict(strict=True)

    question_id: str
    text_fi: str
    type: str
    counts: dict[str, int] | None = None
    mean: float | None = None
    total: int | None = None


class DashboardSummaryOut(BaseModel):
    model_config = ConfigDict(strict=True)

    period: PeriodOut
    total_submissions: int
    by_question: list[QuestionSummaryOut]


class FreetextItemOut(BaseModel):
    model_config = ConfigDict(strict=True)

    text: str


class FreetextPageOut(BaseModel):
    model_config = ConfigDict(strict=True)

    total: int
    page: int
    items: list[FreetextItemOut]
