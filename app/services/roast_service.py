"""Orchestrates roast generation, moderation, and retrieval."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.category import Category
from app.db.models.llm_generation import LLMGeneration
from app.db.models.roast import Roast, RoastModerationStatus
from app.repositories.roast_repository import RoastRepository
from app.services.llm_service import llm_service
from app.services.moderation_service import moderation_service

RECENT_DUPLICATE_CHECK_LIMIT = 500


class RoastService:
    """Coordinates the roast generation pipeline and public retrieval."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = RoastRepository(session)

    async def generate_roast(
        self, category: Category, prompt: str | None = None
    ) -> Roast | None:
        """Generate, moderate, and persist a single roast for a category."""
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

        recent_roasts = await self._repo.list_by_category(category.id)
        recent_content = [
            r.content for r in recent_roasts[:RECENT_DUPLICATE_CHECK_LIMIT]
        ]

        passed = moderation_service.moderate(result["text"], recent_content)
        status = (
            RoastModerationStatus.APPROVED
            if passed
            else RoastModerationStatus.REJECTED
        )

        roast = Roast(
            content=result["text"],
            category_id=category.id,
            status=status,
            llm_generation_id=generation.id,
        )
        await self._repo.create(roast)
        await self._session.commit()

        return roast if passed else None

    async def get_random_roast(self, category_id: int | None = None) -> Roast | None:
        """Return one random approved roast for the public endpoint."""
        return await self._repo.get_random_approved(category_id)