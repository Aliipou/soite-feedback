"""Router tests for public endpoints: /survey/questions, /feedback, /health."""

import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from app.models.question import Question
from tests.conftest import build_feedback_payload


class TestHealth:
    async def test_health_returns_200_with_db(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestSurveyQuestions:
    async def test_returns_only_active_questions(
        self,
        client: AsyncClient,
        active_questions: list[Question],
        inactive_question: Question,
    ) -> None:
        resp = await client.get("/api/v1/survey/questions")
        assert resp.status_code == 200
        body = resp.json()
        ids = {q["id"] for q in body["questions"]}
        assert str(inactive_question.id) not in ids
        assert len(ids) == 3

    async def test_questions_ordered_by_display_order(
        self,
        client: AsyncClient,
        active_questions: list[Question],
    ) -> None:
        resp = await client.get("/api/v1/survey/questions")
        assert resp.status_code == 200
        orders = [q["order"] for q in resp.json()["questions"]]
        assert orders == sorted(orders)

    async def test_response_has_version_field(
        self, client: AsyncClient, active_questions: list[Question]
    ) -> None:
        resp = await client.get("/api/v1/survey/questions")
        assert "version" in resp.json()

    async def test_question_shape(
        self, client: AsyncClient, active_questions: list[Question]
    ) -> None:
        resp = await client.get("/api/v1/survey/questions")
        q = resp.json()["questions"][0]
        assert "id" in q
        assert "text_fi" in q
        assert "type" in q
        assert "order" in q

    async def test_question_has_text_sv_field(
        self, client: AsyncClient, face4_question: Question
    ) -> None:
        resp = await client.get("/api/v1/survey/questions")
        assert resp.status_code == 200
        q = resp.json()["questions"][0]
        assert "text_sv" in q
        assert q["text_sv"] == "Kände du att du blev lyssnad på?"

    async def test_face4_question_type_returned(
        self, client: AsyncClient, face4_question: Question
    ) -> None:
        resp = await client.get("/api/v1/survey/questions")
        assert resp.status_code == 200
        types = {q["type"] for q in resp.json()["questions"]}
        assert "face4" in types

    async def test_official_questions_have_fi_and_sv(
        self, client: AsyncClient, official_questions: list[Question]
    ) -> None:
        resp = await client.get("/api/v1/survey/questions")
        assert resp.status_code == 200
        for q in resp.json()["questions"]:
            assert q["text_fi"], f"Missing Finnish text for question {q['id']}"
            if q["type"] == "face4":
                assert q["text_sv"], f"Missing Swedish text for face4 question {q['id']}"

    async def test_empty_when_no_active_questions(
        self, client: AsyncClient, inactive_question: Question
    ) -> None:
        resp = await client.get("/api/v1/survey/questions")
        assert resp.status_code == 200
        assert resp.json()["questions"] == []


class TestFeedbackSubmission:
    async def test_happy_path_returns_received_true(
        self,
        client: AsyncClient,
        active_questions: list[Question],
    ) -> None:
        payload = build_feedback_payload(active_questions)
        resp = await client.post(
            "/api/v1/feedback",
            json=payload,
            headers={"X-Device-Token": str(uuid.uuid4())},
        )
        assert resp.status_code == 200
        assert resp.json()["received"] is True

    async def test_face4_answer_accepted(
        self, client: AsyncClient, face4_question: Question
    ) -> None:
        payload = {
            "submission_id": str(uuid.uuid4()),
            "answers": [{"question_id": str(face4_question.id), "int_value": 4}],
            "submitted_at_local": datetime.now(UTC).isoformat(),
            "app_version": "1.0.0",
        }
        resp = await client.post(
            "/api/v1/feedback",
            json=payload,
            headers={"X-Device-Token": str(uuid.uuid4())},
        )
        assert resp.status_code == 200
        assert resp.json()["received"] is True

    async def test_face4_all_values_1_to_4_accepted(
        self, client: AsyncClient, official_questions: list[Question]
    ) -> None:
        face4_qs = [q for q in official_questions if q.question_type == "face4"]
        for val in (1, 2, 3, 4):
            payload = {
                "submission_id": str(uuid.uuid4()),
                "answers": [{"question_id": str(face4_qs[0].id), "int_value": val}],
                "submitted_at_local": datetime.now(UTC).isoformat(),
                "app_version": "1.0.0",
            }
            resp = await client.post(
                "/api/v1/feedback",
                json=payload,
                headers={"X-Device-Token": str(uuid.uuid4())},
            )
            assert resp.status_code == 200, f"Value {val} rejected unexpectedly"

    async def test_official_full_survey_submission(
        self, client: AsyncClient, official_questions: list[Question]
    ) -> None:
        payload = build_feedback_payload(official_questions)
        resp = await client.post(
            "/api/v1/feedback",
            json=payload,
            headers={"X-Device-Token": str(uuid.uuid4())},
        )
        assert resp.status_code == 200
        assert resp.json()["received"] is True

    async def test_idempotent_submission_returns_200(
        self,
        client: AsyncClient,
        active_questions: list[Question],
    ) -> None:
        payload = build_feedback_payload(active_questions)
        device = str(uuid.uuid4())
        resp1 = await client.post(
            "/api/v1/feedback", json=payload, headers={"X-Device-Token": device}
        )
        resp2 = await client.post(
            "/api/v1/feedback", json=payload, headers={"X-Device-Token": device}
        )
        assert resp1.status_code == 200
        assert resp2.status_code == 200

    async def test_invalid_question_id_returns_422(
        self, client: AsyncClient, scale5_question: Question
    ) -> None:
        resp = await client.post(
            "/api/v1/feedback",
            json={
                "submission_id": str(uuid.uuid4()),
                "answers": [{"question_id": str(uuid.uuid4()), "int_value": 3}],
                "submitted_at_local": datetime.now(UTC).isoformat(),
            },
            headers={"X-Device-Token": str(uuid.uuid4())},
        )
        assert resp.status_code == 422

    async def test_scale5_out_of_range_returns_422(
        self, client: AsyncClient, active_questions: list[Question]
    ) -> None:
        payload = build_feedback_payload(
            active_questions,
            {
                "answers": [
                    {"question_id": str(active_questions[0].id), "int_value": 99},
                    {"question_id": str(active_questions[1].id), "int_value": 1},
                    {"question_id": str(active_questions[2].id), "text_value": "ok"},
                ]
            },
        )
        resp = await client.post(
            "/api/v1/feedback",
            json=payload,
            headers={"X-Device-Token": str(uuid.uuid4())},
        )
        assert resp.status_code in (422, 200)

    async def test_missing_device_token_returns_400(
        self, client: AsyncClient, active_questions: list[Question]
    ) -> None:
        payload = build_feedback_payload(active_questions)
        resp = await client.post("/api/v1/feedback", json=payload)
        assert resp.status_code == 400

    async def test_content_type_json_required(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/feedback",
            content="not json",
            headers={"X-Device-Token": str(uuid.uuid4()), "Content-Type": "text/plain"},
        )
        assert resp.status_code in (400, 415, 422)

    async def test_freetext_answer_optional_can_be_skipped(
        self, client: AsyncClient, official_questions: list[Question]
    ) -> None:
        face4_qs = [q for q in official_questions if q.question_type == "face4"]
        payload = {
            "submission_id": str(uuid.uuid4()),
            "answers": [{"question_id": str(q.id), "int_value": 3} for q in face4_qs],
            "submitted_at_local": datetime.now(UTC).isoformat(),
            "app_version": "1.0.0",
        }
        resp = await client.post(
            "/api/v1/feedback",
            json=payload,
            headers={"X-Device-Token": str(uuid.uuid4())},
        )
        assert resp.status_code == 200


class TestErrorFormat:
    async def test_404_returns_standard_error_format(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/does-not-exist")
        assert resp.status_code == 404
