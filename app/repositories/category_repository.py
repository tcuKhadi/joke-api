"""Data-access layer for Category records."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.category import Category


class CategoryRepository:
    """Encapsulates all database queries for the Category model."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, category: Category) -> Category:
        """Persist a new category and return it with its generated ID."""
        self._session.add(category)
        await self._session.flush()
        return category

    async def get_by_id(self, category_id: int) -> Category | None:
        """Fetch a single category by its primary key."""
        result = await self._session.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Category | None:
        """Fetch a single category by its slug."""
        result = await self._session.execute(
            select(Category).where(Category.slug == slug)
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Category]:
        """Return all active categories."""
        result = await self._session.execute(
            select(Category).where(Category.is_active.is_(True))
        )
        return list(result.scalars().all())