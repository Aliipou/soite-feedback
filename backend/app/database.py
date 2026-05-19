"""Async SQLAlchemy engine and session factory."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

_is_pg = settings.database_url.startswith("postgresql")
engine = create_async_engine(
    settings.database_url,
    **(
        {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 1800,   # prevent stale TCP connections after idle
            "pool_pre_ping": True,  # detect dropped connections transparently
        }
        if _is_pg
        else {}
    ),
    echo=settings.environment == "development",
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all mapped models."""


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for use outside of FastAPI dependency injection."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields a DB session, commits on success, rolls back on error."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
