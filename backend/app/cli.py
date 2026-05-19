"""Management CLI commands."""

import asyncio
from datetime import UTC, datetime, timedelta

import click

from app.database import get_db_context
from app.security.password import hash_password, validate_password_policy
from app.models.user import StaffUser


@click.group()
def cli() -> None:
    """Soite feedback management commands."""


@cli.command("create-admin")
@click.option("--email", required=True, help="Admin email address")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
def create_admin(email: str, password: str) -> None:
    """Create an admin staff account. Will fail if email already exists."""
    if not validate_password_policy(password):
        click.echo("ERROR: Password must be 12+ chars with uppercase and digit.", err=True)
        raise SystemExit(1)

    async def _run() -> None:
        async with get_db_context() as db:
            user = StaffUser(
                email=email.lower().strip(),
                hashed_password=hash_password(password),
                role="admin",
                is_active=True,
                force_password_change=False,
            )
            db.add(user)
            await db.flush()
            click.echo(f"Admin user created: {user.email} (id={user.id})")

    asyncio.run(_run())


@cli.command("purge-old-data")
@click.option("--dry-run", is_flag=True, default=False)
def purge_old_data(dry_run: bool) -> None:
    """Delete submissions older than 3 years (GDPR retention policy)."""
    cutoff = datetime.now(UTC) - timedelta(days=365 * 3)
    click.echo(f"Purging submissions before {cutoff.date()} {'(dry run)' if dry_run else ''}")

    from app.services.feedback import purge_old_submissions

    async def _run() -> None:
        async with get_db_context() as db:
            if dry_run:
                from sqlalchemy import select, func
                from app.models.feedback import FeedbackSubmission
                result = await db.execute(
                    select(func.count(FeedbackSubmission.id)).where(
                        FeedbackSubmission.submitted_at < cutoff
                    )
                )
                count = result.scalar_one()
                click.echo(f"Would delete {count} submissions (dry run — no changes made)")
            else:
                deleted = await purge_old_submissions(db, cutoff)
                click.echo(f"Deleted {deleted} submissions")

    asyncio.run(_run())


if __name__ == "__main__":
    cli()
