"""Orchestrates joke generation, moderation, and retrieval."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.category import Category
from app.db.models.joke import Joke, ModerationStatus
from app.db.models.llm_generation import LLMGeneration
from app.core.config import settings
from app.repositories.joke_repository import JokeRepository
from app.services.llm_service import llm_service
from app.services.moderation_service import moderation_service

RECENT_DUPLICATE_CHECK_LIMIT = 500


class JokeService:
    """Coordinates the joke generation pipeline and public retrieval."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = JokeRepository(session)

    async def generate_joke(
        self, category: Category, prompt: str | None = None
    ) -> Joke | None:
        """Generate, moderate, and persist a single joke for a category."""
        result = llm_service.generate(prompt or category.prompt_template)

        generation = LLMGeneration(
            prompt=category.prompt_template,
            raw_output=result["text"],
            model_name=settings.llm_model_name,
            latency_ms=result["latency_ms"],
            prompt_tokens=result["prompt_tokens"],
            completion_tokens=result["completion_tokens"],
            temperature=result["temperature"],
            top_p=result["top_p"],
            max_tokens=result["max_tokens"],
        )
        self._session.add(generation)
        await self._session.flush()

        recent_jokes = await self._repo.list_by_category(category.id)
        recent_content = [
            j.content for j in recent_jokes[:RECENT_DUPLICATE_CHECK_LIMIT]
        ]

        passed = moderation_service.moderate(result["text"], recent_content)
        status = (
            ModerationStatus.APPROVED if passed else ModerationStatus.REJECTED
        )

        joke = Joke(
            content=result["text"],
            category_id=category.id,
            status=status,
            llm_generation_id=generation.id,
        )
        await self._repo.create(joke)
        await self._session.commit()

        return joke if passed else None

    async def get_random_joke(self, category_id: int | None = None) -> Joke | None:
        """Return one random approved joke for the public endpoint."""
        return await self._repo.get_random_approved(category_id)