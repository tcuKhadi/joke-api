# scripts/seed_categories.py
"""One-off script to seed initial categories."""
import asyncio

from app.db.session import AsyncSessionLocal
from app.db.models.category import Category

CATEGORIES = [
    dict(
        name="Dad Jokes",
        slug="dad-jokes",
        description="Classic groan-worthy dad humor.",
        prompt_template="Write a short, clean dad joke.",
    ),
    dict(
        name="Puns",
        slug="puns",
        description="Wordplay-based jokes.",
        prompt_template="Write a clever pun-based joke.",
    ),
    dict(
        name="Dark Humor",
        slug="dark-humor",
        description="Edgy, dark comedy.",
        prompt_template="Write a dark humor joke, not punching down at protected groups.",
    ),
    dict(
        name="Roasts",
        slug="roasts",
        description="Used for roast generation.",
        prompt_template="Write a witty, lighthearted roast.",
    ),
]


async def main() -> None:
    async with AsyncSessionLocal() as session:
        for c in CATEGORIES:
            session.add(Category(**c))
        await session.commit()
    print(f"Seeded {len(CATEGORIES)} categories.")


if __name__ == "__main__":
    asyncio.run(main())