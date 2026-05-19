"""Initial schema — all tables, indexes, triggers, pgcrypto, roles.

Revision ID: 0001
Revises:
Create Date: 2026-05-19
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # ── Extension ─────────────────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ── questions ─────────────────────────────────────────────────────────────
    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("text_fi", sa.Text, nullable=False),
        sa.Column("text_en", sa.Text, nullable=True),
        sa.Column("question_type", sa.String(16), nullable=False),
        sa.Column("display_order", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "question_type IN ('scale5', 'yesno', 'text')",
            name="ck_questions_type",
        ),
    )
    op.create_index("idx_questions_active_order", "questions", ["is_active", "display_order"])

    # ── feedback_submissions ──────────────────────────────────────────────────
    op.create_table(
        "feedback_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_submission_id", postgresql.UUID(as_uuid=True),
                  nullable=False, unique=True),
        sa.Column("device_token", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("question_count", sa.SmallInteger, nullable=False),
        sa.Column("app_version", sa.String(16), nullable=True),
    )
    op.create_index(
        "idx_submissions_submitted_at", "feedback_submissions", ["submitted_at"],
        postgresql_ops={"submitted_at": "DESC"}
    )
    op.create_index("idx_submissions_device", "feedback_submissions", ["device_token"])
    op.create_index(
        "idx_submissions_client_id", "feedback_submissions", ["client_submission_id"],
        unique=True
    )

    # ── feedback_answers ──────────────────────────────────────────────────────
    op.create_table(
        "feedback_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("submission_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("feedback_submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("questions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("int_value", sa.SmallInteger, nullable=True),
        sa.Column("text_value", sa.LargeBinary, nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "int_value IS NULL OR (int_value >= 0 AND int_value <= 5)",
            name="ck_answers_int_value_range",
        ),
        sa.UniqueConstraint("submission_id", "question_id", name="uq_submission_question"),
    )
    op.create_index("idx_answers_submission", "feedback_answers", ["submission_id"])
    op.create_index("idx_answers_question", "feedback_answers", ["question_id"])

    # ── staff_users ───────────────────────────────────────────────────────────
    op.create_table(
        "staff_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("hashed_password", sa.Text, nullable=False),
        sa.Column("role", sa.String(16), nullable=False, server_default="staff"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("force_password_change", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("role IN ('staff', 'admin')", name="ck_users_role"),
    )
    op.create_index("idx_users_email", "staff_users", ["email"], unique=True)

    # ── refresh_tokens ────────────────────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("staff_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_refresh_token_hash", "refresh_tokens", ["token_hash"], unique=True)
    op.create_index(
        "idx_refresh_user_active", "refresh_tokens", ["user_id"],
        postgresql_where=sa.text("revoked_at IS NULL"),
    )
    op.create_index(
        "idx_refresh_expires", "refresh_tokens", ["expires_at"],
        postgresql_where=sa.text("revoked_at IS NULL"),
    )

    # ── audit_log ─────────────────────────────────────────────────────────────
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("staff_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("before_json", postgresql.JSONB, nullable=True),
        sa.Column("after_json", postgresql.JSONB, nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
    )

    # ── Trigger: auto-update questions.updated_at ─────────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN NEW.updated_at = now(); RETURN NEW; END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER trg_questions_updated_at
        BEFORE UPDATE ON questions
        FOR EACH ROW EXECUTE FUNCTION update_updated_at()
    """)

    # ── Seed: default questions ────────────────────────────────────────────────
    op.execute("""
        INSERT INTO questions (text_fi, text_en, question_type, display_order) VALUES
        ('Kuinka tyytyväinen olit saamaasi hoitoon?',
         'How satisfied were you with the care you received?', 'scale5', 1),
        ('Saitko riittävästi tietoa kuntoutuksestasi?',
         'Did you receive enough information about your rehabilitation?', 'yesno', 2),
        ('Haluatko antaa muuta palautetta?',
         'Would you like to give any other feedback?', 'text', 3)
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_questions_updated_at ON questions")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at")
    op.drop_table("audit_log")
    op.drop_table("refresh_tokens")
    op.drop_table("staff_users")
    op.drop_table("feedback_answers")
    op.drop_table("feedback_submissions")
    op.drop_table("questions")
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
