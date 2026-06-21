"""Data-access layer for Roast records."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.roast import Roast, RoastModerationStatus


class RoastRepository:
    """Encapsulates all database queries for the Roast model."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, roast: Roast) -> Roast:
        """Persist a new roast and return it with its generated ID."""
        self._session.add(roast)
        await self._session.flush()
        return roast

    async def get_by_id(self, roast_id: int) -> Roast | None:
        """Fetch a single roast by its primary key."""
        result = await self._session.execute(
            select(Roast).where(Roast.id == roast_id)
        )
        return result.scalar_one_or_none()

    async def get_random_approved(
        self, category_id: int | None = None
    ) -> Roast | None:
        """Return one random approved roast, optionally filtered by category."""
        query = select(Roast).where(
            Roast.status == RoastModerationStatus.APPROVED
        )
        if category_id is not None:
            query = query.where(Roast.category_id == category_id)
        query = query.order_by(func.random()).limit(1)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_two_for_battle(
        self, category_id: int | None = None
    ) -> tuple[Roast, Roast] | None:
        """Return two distinct random approved roasts for a battle."""
        query = select(Roast).where(
            Roast.status == RoastModerationStatus.APPROVED
        )
        if category_id is not None:
            query = query.where(Roast.category_id == category_id)
        query = query.order_by(func.random()).limit(2)
        result = await self._session.execute(query)
        roasts = result.scalars().all()
        if len(roasts) < 2:
            return None
        return roasts[0], roasts[1]

    async def update_elo(
        self, roast_id: int, new_score: float, battle_count: int
    ) -> None:
        """Update a roast's ELO score and battle count after a battle."""
        roast = await self.get_by_id(roast_id)
        if roast is None:
            return
        roast.elo_score = new_score
        roast.battle_count = battle_count
        await self._session.flush()

    async def list_by_category(
        self,
        category_id: int,
        status: RoastModerationStatus = RoastModerationStatus.APPROVED,
    ) -> list[Roast]:
        """Return all roasts in a category with the given moderation status."""
        result = await self._session.execute(
            select(Roast)
            .where(Roast.category_id == category_id)
            .where(Roast.status == status)
        )
        return list(result.scalars().all())