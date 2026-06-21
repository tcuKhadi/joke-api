"""Pydantic schemas for Roast serialization."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.db.models.roast import RoastModerationStatus


class RoastResponse(BaseModel):
    """Public-facing representation of a roast."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    category_id: int
    elo_score: float
    battle_count: int
    created_at: datetime


class RoastCreate(BaseModel):
    """Internal schema used when inserting a newly generated roast."""

    content: str
    category_id: int
    status: RoastModerationStatus = RoastModerationStatus.PENDING
    llm_generation_id: int | None = None