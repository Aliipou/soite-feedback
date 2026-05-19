"""Staff user management service."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AuditLog, StaffUser
from app.security.password import hash_password


async def get_user_by_email(db: AsyncSession, email: str) -> StaffUser | None:
    """Return user by email address, or None."""
    result = await db.execute(
        select(StaffUser).where(StaffUser.email == email)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> StaffUser | None:
    """Return user by ID, or None."""
    result = await db.execute(
        select(StaffUser).where(StaffUser.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_all_users(db: AsyncSession) -> list[StaffUser]:
    """Return all staff users ordered by email."""
    result = await db.execute(select(StaffUser).order_by(StaffUser.email))
    return list(result.scalars().all())


async def create_user(
    db: AsyncSession,
    email: str,
    password: str,
    role: str,
    actor_id: uuid.UUID,
) -> StaffUser:
    """Create a staff user with bcrypt-hashed password and write audit log."""
    user = StaffUser(
        email=email.lower().strip(),
        hashed_password=hash_password(password),
        role=role,
        is_active=True,
        force_password_change=True,
    )
    db.add(user)
    await db.flush()

    db.add(AuditLog(
        actor_id=actor_id,
        action="user.create",
        target_id=user.id,
        after_json={"email": user.email, "role": user.role},
    ))
    return user


async def update_user(
    db: AsyncSession,
    user: StaffUser,
    actor_id: uuid.UUID,
    is_active: bool | None = None,
    role: str | None = None,
) -> StaffUser:
    """Update user fields and write audit log."""
    before = {"is_active": user.is_active, "role": user.role}

    if is_active is not None:
        user.is_active = is_active
    if role is not None:
        user.role = role
    await db.flush()

    db.add(AuditLog(
        actor_id=actor_id,
        action="user.update",
        target_id=user.id,
        before_json=before,
        after_json={"is_active": user.is_active, "role": user.role},
    ))
    return user
