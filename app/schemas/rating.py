"""Pydantic schemas for battle/rating serialization."""

from pydantic import BaseModel

from app.db.models.rating import ContentType


class BattleItem(BaseModel):
    """A single content item presented in a battle."""

    content_type: ContentType
    content_id: int
    content: str


class BattlePairResponse(BaseModel):
    """Two items presented for head-to-head voting."""

    battle_id: str
    challenger: BattleItem
    opponent: BattleItem


class VoteRequest(BaseModel):
    """Client's submitted vote for a previously served battle."""

    battle_id: str
    winner_type: ContentType
    winner_id: int


class RatingResponse(BaseModel):
    """Result of a recorded vote, including updated ELO deltas."""

    id: int
    challenger_elo_before: float
    opponent_elo_before: float
    challenger_elo_delta: float
    opponent_elo_delta: float