"""API routes for joke retrieval and generation."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import limiter
from app.db.session import get_db
from app.repositories.category_repository import CategoryRepository
from app.repositories.joke_repository import JokeRepository
from app.schemas.joke import JokeResponse
from app.services.joke_service import JokeService

router = APIRouter(prefix="/jokes", tags=["jokes"])


@router.get("/random", response_model=JokeResponse)
async def get_random_joke(
    category_id: int | None = None, db: AsyncSession = Depends(get_db)
):
    """Return one random approved joke, optionally filtered by category."""
    repo = JokeRepository(db)
    joke = await repo.get_random_approved(category_id)
    if joke is None:
        raise HTTPException(status_code=404, detail="No joke available")
    return joke


@router.get("/{joke_id}", response_model=JokeResponse)
async def get_joke(joke_id: int, db: AsyncSession = Depends(get_db)):
    """Return a single joke by ID."""
    repo = JokeRepository(db)
    joke = await repo.get_by_id(joke_id)
    if joke is None:
        raise HTTPException(status_code=404, detail="Joke not found")
    return joke


@router.post("/generate/{category_id}", status_code=202)
@limiter.limit("5/minute")
async def trigger_generation(
    request: Request,
    category_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Queue a single joke generation for the given category."""
    category_repo = CategoryRepository(db)
    category = await category_repo.get_by_id(category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    service = JokeService(db)
    background_tasks.add_task(service.generate_joke, category)

    return {"status": "queued", "category_id": category_id}