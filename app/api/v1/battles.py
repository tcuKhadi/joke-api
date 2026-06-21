"""API routes for joke/roast head-to-head battles."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import limiter
from app.db.models.rating import ContentType
from app.db.session import get_db
from app.schemas.rating import BattlePairResponse, RatingResponse, VoteRequest
from app.services.battle_service import BattleService

router = APIRouter(prefix="/battles", tags=["battles"])


@router.get("", response_model=BattlePairResponse)
@limiter.limit("30/minute")
async def get_battle(
    request: Request,
    category_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Return two random approved items for head-to-head voting."""
    service = BattleService(db)
    pair = await service.get_battle_pair(category_id)
    if pair is None:
        raise HTTPException(status_code=404, detail="Not enough content to battle")
    return pair


@router.post("/vote", response_model=RatingResponse)
@limiter.limit("30/minute")
async def submit_vote(
    request: Request,
    payload: VoteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit a vote for a previously served battle pairing."""
    service = BattleService(db)
    rating = await service.submit_vote(
        battle_id=payload.battle_id,
        winner_type=payload.winner_type,
        winner_id=payload.winner_id,
    )
    if rating is None:
        raise HTTPException(
            status_code=400, detail="Invalid or expired battle"
        )
    return rating