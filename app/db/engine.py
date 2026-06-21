"""Async SQLAlchemy engine for the application."""

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import settings

engine: AsyncEngine = create_async_engine(
    str(settings.database_url),
    echo=settings.environment == "development",
    pool_pre_ping=True,
)