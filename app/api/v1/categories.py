"""API routes for category management and retrieval."""

import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.category import Category
from app.db.session import get_db
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryResponse

ALLOWED_TOPIC_PATTERN = re.compile(r"^[A-Za-z0-9 ,'\-]{3,80}$")
PROMPT_TEMPLATE = (
    "Write a short, original, family-appropriate joke about {topic}. "
    "Keep it under 3 sentences."
)

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """Return all active categories."""
    repo = CategoryRepository(db)
    return await repo.list_active()


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)):
    """Return a single category by ID."""
    repo = CategoryRepository(db)
    category = await repo.get_by_id(category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.post("", response_model=CategoryResponse, status_code=201)
async def create_category(
    payload: CategoryCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new category."""
    if not ALLOWED_TOPIC_PATTERN.match(payload.topic):
        raise HTTPException(status_code=422, detail="Invalid topic format")

    repo = CategoryRepository(db)
    existing = await repo.get_by_slug(payload.slug)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Slug already exists")

    category = Category(
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        prompt_template=PROMPT_TEMPLATE.format(topic=payload.topic),
    )
    await repo.create(category)
    await db.commit()
    return category