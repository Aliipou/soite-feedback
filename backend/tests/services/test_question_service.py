"""Unit tests for question and user services."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question
from app.models.user import AuditLog, StaffUser
from app.services import question as question_svc
from app.services import user as user_svc


class TestQuestionService:
    async def test_get_active_questions_excludes_inactive(
        self,
        db: AsyncSession,
        active_questions: list[Question],
        inactive_question: Question,
    ) -> None:
        results = await question_svc.get_active_questions(db)
        ids = {q.id for q in results}
        assert inactive_question.id not in ids
        assert len(ids) == 3

    async def test_get_active_questions_ordered(
        self, db: AsyncSession, active_questions: list[Question]
    ) -> None:
        results = await question_svc.get_active_questions(db)
        orders = [q.display_order for q in results]
        assert orders == sorted(orders)

    async def test_get_all_questions_includes_inactive(
        self,
        db: AsyncSession,
        active_questions: list[Question],
        inactive_question: Question,
    ) -> None:
        results = await question_svc.get_all_questions(db)
        ids = {q.id for q in results}
        assert inactive_question.id in ids

    async def test_create_question_writes_audit_log(
        self, db: AsyncSession, admin_user: StaffUser
    ) -> None:
        q = await question_svc.create_question(
            db,
            text_fi="Test?",
            text_sv="Test?",
            question_type="face4",
            display_order=10,
            actor_id=admin_user.id,
        )
        from sqlalchemy import select
        logs = await db.execute(
            select(AuditLog).where(
                AuditLog.target_id == q.id,
                AuditLog.action == "question.create",
            )
        )
        assert logs.scalar_one_or_none() is not None

    async def test_create_question_stores_sv_text(
        self, db: AsyncSession, admin_user: StaffUser
    ) -> None:
        q = await question_svc.create_question(
            db,
            text_fi="Suomenkielinen kysymys?",
            text_sv="Svensk fråga?",
            question_type="face4",
            display_order=10,
            actor_id=admin_user.id,
        )
        assert q.text_sv == "Svensk fråga?"

    async def test_create_question_strips_html(
        self, db: AsyncSession, admin_user: StaffUser
    ) -> None:
        q = await question_svc.create_question(
            db,
            text_fi="<b>Bold</b> question?",
            text_sv=None,
            question_type="yesno",
            display_order=5,
            actor_id=admin_user.id,
        )
        assert "<b>" not in q.text_fi

    async def test_create_face4_question_type_accepted(
        self, db: AsyncSession, admin_user: StaffUser
    ) -> None:
        q = await question_svc.create_question(
            db,
            text_fi="Hymynaama?",
            text_sv="Smiley?",
            question_type="face4",
            display_order=20,
            actor_id=admin_user.id,
        )
        assert q.question_type == "face4"

    async def test_update_question_sv_text(
        self, db: AsyncSession, admin_user: StaffUser, scale5_question: Question
    ) -> None:
        updated = await question_svc.update_question(
            db, scale5_question, admin_user.id, text_sv="Uppdaterad fråga?"
        )
        assert updated.text_sv == "Uppdaterad fråga?"

    async def test_update_question_writes_before_after_audit(
        self, db: AsyncSession, admin_user: StaffUser, scale5_question: Question
    ) -> None:
        from sqlalchemy import select
        old_text = scale5_question.text_fi
        await question_svc.update_question(
            db, scale5_question, admin_user.id, text_fi="Updated text?", is_active=False
        )
        logs = await db.execute(
            select(AuditLog).where(
                AuditLog.target_id == scale5_question.id,
                AuditLog.action == "question.update",
            )
        )
        log = logs.scalar_one_or_none()
        assert log is not None
        assert log.before_json is not None
        assert log.before_json["text_fi"] == old_text
        assert log.after_json is not None
        assert log.after_json["is_active"] is False

    async def test_get_question_by_id_returns_none_for_missing(
        self, db: AsyncSession
    ) -> None:
        result = await question_svc.get_question_by_id(db, uuid.uuid4())
        assert result is None

    async def test_official_face4_questions_available(
        self, db: AsyncSession, official_questions: list[Question]
    ) -> None:
        active = await question_svc.get_active_questions(db)
        face4_count = sum(1 for q in active if q.question_type == "face4")
        text_count = sum(1 for q in active if q.question_type == "text")
        assert face4_count == 5
        assert text_count == 1

    async def test_official_questions_have_sv_text(
        self, db: AsyncSession, official_questions: list[Question]
    ) -> None:
        active = await question_svc.get_active_questions(db)
        for q in active:
            if q.question_type == "face4":
                assert q.text_sv is not None, f"Question {q.text_fi!r} missing Swedish text"


class TestUserService:
    async def test_create_user_hashes_password(
        self, db: AsyncSession, admin_user: StaffUser
    ) -> None:
        user = await user_svc.create_user(
            db, "new@soite.fi", "NewPass123!", "staff", admin_user.id
        )
        assert user.hashed_password != "NewPass123!"
        assert user.hashed_password.startswith("$2b$")

    async def test_create_user_lowercases_email(
        self, db: AsyncSession, admin_user: StaffUser
    ) -> None:
        user = await user_svc.create_user(
            db, "UPPER@Soite.FI", "NewPass123!", "staff", admin_user.id
        )
        assert user.email == "upper@soite.fi"

    async def test_create_user_writes_audit_log(
        self, db: AsyncSession, admin_user: StaffUser
    ) -> None:
        from sqlalchemy import select
        user = await user_svc.create_user(
            db, "audit@soite.fi", "AuditPass123!", "staff", admin_user.id
        )
        logs = await db.execute(
            select(AuditLog).where(
                AuditLog.target_id == user.id,
                AuditLog.action == "user.create",
            )
        )
        assert logs.scalar_one_or_none() is not None

    async def test_update_user_deactivate_writes_audit(
        self, db: AsyncSession, admin_user: StaffUser, staff_user: StaffUser
    ) -> None:
        from sqlalchemy import select
        await user_svc.update_user(
            db, staff_user, admin_user.id, is_active=False
        )
        logs = await db.execute(
            select(AuditLog).where(
                AuditLog.target_id == staff_user.id,
                AuditLog.action == "user.update",
            )
        )
        log = logs.scalar_one_or_none()
        assert log is not None
        assert log.after_json["is_active"] is False

    async def test_get_user_by_email_returns_none_for_missing(
        self, db: AsyncSession
    ) -> None:
        result = await user_svc.get_user_by_email(db, "nonexistent@soite.fi")
        assert result is None

    async def test_get_user_by_id_returns_user(
        self, db: AsyncSession, staff_user: StaffUser
    ) -> None:
        result = await user_svc.get_user_by_id(db, staff_user.id)
        assert result is not None
        assert result.id == staff_user.id

    async def test_get_user_by_id_returns_none_for_missing(
        self, db: AsyncSession
    ) -> None:
        result = await user_svc.get_user_by_id(db, uuid.uuid4())
        assert result is None

    async def test_get_all_users_returns_list(
        self, db: AsyncSession, staff_user: StaffUser, admin_user: StaffUser
    ) -> None:
        users = await user_svc.get_all_users(db)
        ids = {u.id for u in users}
        assert staff_user.id in ids
        assert admin_user.id in ids

    async def test_update_user_role_only(
        self, db: AsyncSession, admin_user: StaffUser, staff_user: StaffUser
    ) -> None:
        updated = await user_svc.update_user(db, staff_user, admin_user.id, role="admin")
        assert updated.role == "admin"
        assert updated.is_active is True  # unchanged

    async def test_update_user_audit_captures_before_state(
        self, db: AsyncSession, admin_user: StaffUser, staff_user: StaffUser
    ) -> None:
        from sqlalchemy import select
        old_role = staff_user.role
        await user_svc.update_user(db, staff_user, admin_user.id, role="admin")
        logs = await db.execute(
            select(AuditLog).where(
                AuditLog.target_id == staff_user.id,
                AuditLog.action == "user.update",
            )
        )
        log = logs.scalar_one_or_none()
        assert log is not None
        assert log.before_json["role"] == old_role
        assert log.after_json["role"] == "admin"
