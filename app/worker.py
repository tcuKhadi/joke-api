"""Standalone background worker: continuously generates jokes and roasts."""

import asyncio
import random

from app.core.logging import configure_logging, get_logger
from app.db.session import AsyncSessionLocal
from app.repositories.category_repository import CategoryRepository
from app.services.joke_service import JokeService
from app.services.roast_service import RoastService

GENERATION_DELAY_SECONDS = 1.5

STYLE_PREFIXES = [
    "Make it a classic pun.",
    "Make it a one-liner.",
    "Make it observational humor.",
    "Make it a knock-knock joke.",
    "Make it absurd and unexpected.",
]

logger = get_logger(__name__)


def _styled_prompt(base_prompt: str) -> str:
    """Append a randomly chosen style instruction to the base prompt."""
    style = random.choice(STYLE_PREFIXES)
    return f"{base_prompt} {style}"


async def run_cycle() -> None:
    """Generate one joke and one roast for every active category."""
    async with AsyncSessionLocal() as session:
        category_repo = CategoryRepository(session)
        categories = await category_repo.list_active()

    if not categories:
        logger.warning("worker_no_active_categories")
        return

    for category in categories:
        prompt = _styled_prompt(category.prompt_template)

        async with AsyncSessionLocal() as session:
            joke_service = JokeService(session)
            try:
                joke = await joke_service.generate_joke(category, prompt=prompt)
                logger.info(
                    "worker_joke_generated",
                    category_id=category.id,
                    approved=joke is not None,
                )
            except Exception:
                logger.exception(
                    "worker_joke_generation_failed", category_id=category.id
                )

        await asyncio.sleep(GENERATION_DELAY_SECONDS)

        prompt = _styled_prompt(category.prompt_template)

        async with AsyncSessionLocal() as session:
            roast_service = RoastService(session)
            try:
                roast = await roast_service.generate_roast(category, prompt=prompt)
                logger.info(
                    "worker_roast_generated",
                    category_id=category.id,
                    approved=roast is not None,
                )
            except Exception:
                logger.exception(
                    "worker_roast_generation_failed", category_id=category.id
                )

        await asyncio.sleep(GENERATION_DELAY_SECONDS)


async def main() -> None:
    """Run generation cycles forever, looping over all active categories."""
    configure_logging()
    logger.info("worker_started")
    while True:
        try:
            await run_cycle()
        except Exception:
            logger.exception("worker_cycle_failed")
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())