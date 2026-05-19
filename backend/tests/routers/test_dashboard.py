"""Router tests for dashboard endpoints (staff JWT required)."""

import uuid
from datetime import UTC, datetime

from httpx import AsyncClient

from app.models.question import Question
from tests.conftest import build_feedback_payload


class TestDashboardSummary:
    async def test_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 401

    async def test_returns_summary_shape(
        self, client: AsyncClient, staff_token: str, active_questions: list[Question]
    ) -> None:
        resp = await client.get(
            "/api/v1/dashboard/summary",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "total_submissions" in body
        assert "by_question" in body
        assert "period" in body

    async def test_invalid_date_format_returns_400(
        self, client: AsyncClient, staff_token: str
    ) -> None:
        resp = await client.get(
            "/api/v1/dashboard/summary?from=not-a-date",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert resp.status_code == 400

    async def test_total_reflects_submitted_feedback(
        self,
        client: AsyncClient,
        staff_token: str,
        active_questions: list[Question],
    ) -> None:
        device = str(uuid.uuid4())
        for _ in range(3):
            payload = build_feedback_payload(active_questions)
            await client.post(
                "/api/v1/feedback", json=payload, headers={"X-Device-Token": device}
            )

        resp = await client.get(
            "/api/v1/dashboard/summary",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total_submissions"] >= 3

    async def test_staff_token_accepted(
        self, client: AsyncClient, staff_token: str
    ) -> None:
        resp = await client.get(
            "/api/v1/dashboard/summary",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert resp.status_code == 200


class TestDashboardFreetext:
    async def test_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.get(f"/api/v1/dashboard/freetext?question_id={uuid.uuid4()}")
        assert resp.status_code == 401

    async def test_non_text_question_returns_404(
        self,
        client: AsyncClient,
        staff_token: str,
        scale5_question: Question,
    ) -> None:
        resp = await client.get(
            f"/api/v1/dashboard/freetext?question_id={scale5_question.id}",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert resp.status_code == 404

    async def test_text_question_returns_page_shape(
        self,
        client: AsyncClient,
        staff_token: str,
        text_question: Question,
    ) -> None:
        resp = await client.get(
            f"/api/v1/dashboard/freetext?question_id={text_question.id}",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "total" in body
        assert "page" in body
        assert "items" in body

    async def test_nonexistent_question_returns_404(
        self, client: AsyncClient, staff_token: str
    ) -> None:
        resp = await client.get(
            f"/api/v1/dashboard/freetext?question_id={uuid.uuid4()}",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert resp.status_code == 404


class TestAdminEndpoints:
    async def test_staff_cannot_access_questions(
        self, client: AsyncClient, staff_token: str
    ) -> None:
        resp = await client.get(
            "/api/v1/admin/questions",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert resp.status_code == 403

    async def test_admin_list_questions(
        self,
        client: AsyncClient,
        admin_token: str,
        active_questions: list[Question],
    ) -> None:
        resp = await client.get(
            "/api/v1/admin/questions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_admin_create_question(
        self, client: AsyncClient, admin_token: str
    ) -> None:
        resp = await client.post(
            "/api/v1/admin/questions",
            json={"text_fi": "Test question?", "type": "scale5", "order": 10},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["text_fi"] == "Test question?"

    async def test_admin_update_question_active_status(
        self,
        client: AsyncClient,
        admin_token: str,
        scale5_question: Question,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/admin/questions/{scale5_question.id}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    async def test_admin_update_nonexistent_question_returns_404(
        self, client: AsyncClient, admin_token: str
    ) -> None:
        resp = await client.patch(
            f"/api/v1/admin/questions/{uuid.uuid4()}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

    async def test_admin_list_users(
        self,
        client: AsyncClient,
        admin_token: str,
        staff_user,
    ) -> None:
        resp = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_admin_create_user_weak_password_returns_422(
        self, client: AsyncClient, admin_token: str
    ) -> None:
        resp = await client.post(
            "/api/v1/admin/users",
            json={"email": "new@soite.fi", "password": "weak", "role": "staff"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422

    async def test_admin_export_csv_returns_csv(
        self,
        client: AsyncClient,
        admin_token: str,
        active_questions: list[Question],
    ) -> None:
        # Submit some feedback first
        device = str(uuid.uuid4())
        await client.post(
            "/api/v1/feedback",
            json=build_feedback_payload(active_questions),
            headers={"X-Device-Token": device},
        )
        resp = await client.get(
            "/api/v1/admin/export",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert "csv" in resp.headers.get("content-type", "").lower()
