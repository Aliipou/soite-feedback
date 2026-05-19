"""Add text_sv column, face4 question type, and seed official questions.

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-19
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # Add Swedish text column
    op.add_column("questions", sa.Column("text_sv", sa.Text, nullable=True))

    # Expand question_type CHECK constraint to include face4
    op.drop_constraint("ck_questions_type", "questions")
    op.create_check_constraint(
        "ck_questions_type",
        "questions",
        "question_type IN ('scale5', 'yesno', 'text', 'face4')",
    )

    # Deactivate the old placeholder questions (order 1–3 from initial seed)
    op.execute("UPDATE questions SET is_active = false WHERE display_order IN (1, 2, 3)")

    # Insert the official Soite kotikuntoutus questions (FI + SV)
    op.execute("""
        INSERT INTO questions (text_fi, text_sv, question_type, display_order, is_active) VALUES
        (
            'Tunsitko, että sinua kuunneltiin ja sinua kohdeltiin kunnioittavasti?',
            'Kände du att du blev lyssnad på och behandlad med respekt?',
            'face4', 10, true
        ),
        (
            'Saitko tarvitsemaasi apua ja ohjausta jakson aikana?',
            'Fick du den hjälp och vägledning du behövde under perioden?',
            'face4', 20, true
        ),
        (
            'Koetko, että hoitoasi koskevat päätökset tehtiin yhteistyössä kanssasi?',
            'Fattades besluten om din vård i samarbete med dig?',
            'face4', 30, true
        ),
        (
            'Koetko, että toimintakykysi on parantunut jakson myötä?',
            'Upplever du att din funktionsförmåga har förbättrats under perioden?',
            'face4', 40, true
        ),
        (
            'Kuinka todennäköisesti suosittelisit palvelua vastaavassa tilanteessa olevalle?',
            'Hur sannolikt är det att du skulle rekommendera tjänsten till någon i en liknande situation?',
            'face4', 50, true
        ),
        (
            'Vapaa sana ja kehitysideat: Tähän voit kirjoittaa terveisiä työntekijöille tai parannusehdotuksia',
            'Fritt ord och utvecklingsidéer: Du kan skriva hälsningar till personalen eller förbättringsförslag',
            'text', 60, true
        )
    """)


def downgrade() -> None:
    # Remove the new questions and restore the old ones
    op.execute("DELETE FROM questions WHERE display_order IN (10, 20, 30, 40, 50, 60)")
    op.execute("UPDATE questions SET is_active = true WHERE display_order IN (1, 2, 3)")

    # Revert CHECK constraint
    op.drop_constraint("ck_questions_type", "questions")
    op.create_check_constraint(
        "ck_questions_type",
        "questions",
        "question_type IN ('scale5', 'yesno', 'text')",
    )

    # Remove text_sv column
    op.drop_column("questions", "text_sv")
