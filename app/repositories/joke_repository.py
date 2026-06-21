"""Data-access layer for Joke records."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.joke import Joke, ModerationStatus


class JokeRepository:
    """Encapsulates all database queries for the Joke model."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, joke: Joke) -> Joke:
        """Persist a new joke and return it with its generated ID."""
        self._session.add(joke)
        await self._session.flush()
        return joke

    async def get_by_id(self, joke_id: int) -> Joke | None:
        """Fetch a single joke by its primary key."""
        result = await self._session.execute(
            select(Joke).where(Joke.id == joke_id)
        )
        return result.scalar_one_or_none()

    async def get_random_approved(
        self, category_id: int | None = None
    ) -> Joke | None:
        """Return one random approved joke, optionally filtered by category."""
        query = select(Joke).where(Joke.status == ModerationStatus.APPROVED)
        if category_id is not None:
            query = query.where(Joke.category_id == category_id)
        query = query.order_by(func.random()).limit(1)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_two_for_battle(
        self, category_id: int | None = None
    ) -> tuple[Joke, Joke] | None:
        """Return two distinct random approved jokes for a battle."""
        query = select(Joke).where(Joke.status == ModerationStatus.APPROVED)
        if category_id is not None:
            query = query.where(Joke.category_id == category_id)
        query = query.order_by(func.random()).limit(2)
        result = await self._session.execute(query)
        jokes = result.scalars().all()
        if len(jokes) < 2:
            return None
        return jokes[0], jokes[1]

    async def update_elo(
        self, joke_id: int, new_score: float, battle_count: int
    ) -> None:
        """Update a joke's ELO score and battle count after a battle."""
        joke = await self.get_by_id(joke_id)
        if joke is None:
            return
        joke.elo_score = new_score
        joke.battle_count = battle_count
        await self._session.flush()

    async def list_by_category(
        self,
        category_id: int,
        status: ModerationStatus = ModerationStatus.APPROVED,
    ) -> list[Joke]:
        """Return all jokes in a category with the given moderation status."""
        result = await self._session.execute(
            select(Joke)
            .where(Joke.category_id == category_id)
            .where(Joke.status == status)
        )
        return list(result.scalars().all())