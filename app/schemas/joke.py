"""Pydantic schemas for Joke serialization."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.db.models.joke import ModerationStatus


class JokeResponse(BaseModel):
    """Public-facing representation of a joke."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    category_id: int
    elo_score: float
    battle_count: int
    created_at: datetime


class JokeCreate(BaseModel):
    """Internal schema used when inserting a newly generated joke."""

    content: str
    category_id: int
    status: ModerationStatus = ModerationStatus.PENDING
    llm_generation_id: int | None = None