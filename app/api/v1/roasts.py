"""API routes for roast retrieval and generation."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import limiter
from app.db.session import get_db
from app.repositories.category_repository import CategoryRepository
from app.repositories.roast_repository import RoastRepository
from app.schemas.roast import RoastResponse
from app.services.roast_service import RoastService

router = APIRouter(prefix="/roasts", tags=["roasts"])


@router.get("/random", response_model=RoastResponse)
async def get_random_roast(
    category_id: int | None = None, db: AsyncSession = Depends(get_db)
):
    """Return one random approved roast, optionally filtered by category."""
    repo = RoastRepository(db)
    roast = await repo.get_random_approved(category_id)
    if roast is None:
        raise HTTPException(status_code=404, detail="No roast available")
    return roast


@router.get("/{roast_id}", response_model=RoastResponse)
async def get_roast(roast_id: int, db: AsyncSession = Depends(get_db)):
    """Return a single roast by ID."""
    repo = RoastRepository(db)
    roast = await repo.get_by_id(roast_id)
    if roast is None:
        raise HTTPException(status_code=404, detail="Roast not found")
    return roast


@router.post("/generate/{category_id}", status_code=202)
@limiter.limit("5/minute")
async def trigger_generation(
    request: Request,
    category_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Queue a single roast generation for the given category."""
    category_repo = CategoryRepository(db)
    category = await category_repo.get_by_id(category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    service = RoastService(db)
    background_tasks.add_task(service.generate_roast, category)

    return {"status": "queued", "category_id": category_id}