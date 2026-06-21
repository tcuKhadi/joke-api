"""Orchestrates head-to-head battles between jokes and/or roasts."""

import random
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.rating import ContentType, Rating
from app.repositories.joke_repository import JokeRepository
from app.repositories.roast_repository import RoastRepository
from app.schemas.rating import BattleItem, BattlePairResponse
from app.services.cache_service import cache_service

K_FACTOR = 32
BATTLE_PAIRING_TTL_SECONDS = 300


class BattleService:
    """Coordinates serving battle pairs and recording vote outcomes."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._joke_repo = JokeRepository(session)
        self._roast_repo = RoastRepository(session)

    def _expected_score(self, rating_a: float, rating_b: float) -> float:
        """Return the expected win probability of A against B."""
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def _new_elo(self, rating: float, expected: float, actual: float) -> float:
        """Return the updated ELO rating after one battle."""
        return rating + K_FACTOR * (actual - expected)

    def _get_repo(self, content_type: ContentType):
        """Return the repository matching the given content type."""
        if content_type == ContentType.JOKE:
            return self._joke_repo
        return self._roast_repo

    async def _pick_item(self, category_id: int | None):
        """Randomly select a joke or roast repository, then fetch one item."""
        content_type = random.choice([ContentType.JOKE, ContentType.ROAST])
        repo = self._get_repo(content_type)
        item = await repo.get_random_approved(category_id)
        if item is None:
            other_type = (
                ContentType.ROAST
                if content_type == ContentType.JOKE
                else ContentType.JOKE
            )
            repo = self._get_repo(other_type)
            item = await repo.get_random_approved(category_id)
            content_type = other_type
        return content_type, item

    async def get_battle_pair(
        self, category_id: int | None = None
    ) -> BattlePairResponse | None:
        """Serve two random approved items, possibly mixed type, for voting."""
        challenger_type, challenger = await self._pick_item(category_id)
        opponent_type, opponent = await self._pick_item(category_id)

        if challenger is None or opponent is None:
            return None
        if challenger_type == opponent_type and challenger.id == opponent.id:
            return None

        battle_id = str(uuid.uuid4())
        await cache_service.set(
            f"battle:{battle_id}",
            {
                "challenger_type": challenger_type.value,
                "challenger_id": challenger.id,
                "opponent_type": opponent_type.value,
                "opponent_id": opponent.id,
            },
            ttl_seconds=BATTLE_PAIRING_TTL_SECONDS,
        )

        return BattlePairResponse(
            battle_id=battle_id,
            challenger=BattleItem(
                content_type=challenger_type,
                content_id=challenger.id,
                content=challenger.content,
            ),
            opponent=BattleItem(
                content_type=opponent_type,
                content_id=opponent.id,
                content=opponent.content,
            ),
        )

    async def submit_vote(
        self,
        battle_id: str,
        winner_type: ContentType,
        winner_id: int,
        voter_id: int | None = None,
    ) -> Rating | None:
        """Validate a vote against its served pairing and apply ELO updates."""
        cache_key = f"battle:{battle_id}"
        pairing = await cache_service.get(cache_key)
        if pairing is None:
            return None
        await cache_service.delete(cache_key)

        challenger_type = ContentType(pairing["challenger_type"])
        opponent_type = ContentType(pairing["opponent_type"])
        challenger_id = pairing["challenger_id"]
        opponent_id = pairing["opponent_id"]

        if winner_id not in (challenger_id, opponent_id):
            return None

        challenger_repo = self._get_repo(challenger_type)
        opponent_repo = self._get_repo(opponent_type)

        challenger = await challenger_repo.get_by_id(challenger_id)
        opponent = await opponent_repo.get_by_id(opponent_id)
        if challenger is None or opponent is None:
            return None

        challenger_won = 1.0 if winner_id == challenger_id else 0.0
        opponent_won = 1.0 - challenger_won

        expected_challenger = self._expected_score(
            challenger.elo_score, opponent.elo_score
        )
        expected_opponent = 1 - expected_challenger

        new_challenger_elo = self._new_elo(
            challenger.elo_score, expected_challenger, challenger_won
        )
        new_opponent_elo = self._new_elo(
            opponent.elo_score, expected_opponent, opponent_won
        )

        challenger_delta = new_challenger_elo - challenger.elo_score
        opponent_delta = new_opponent_elo - opponent.elo_score

        await challenger_repo.update_elo(
            challenger_id, new_challenger_elo, challenger.battle_count + 1
        )
        await opponent_repo.update_elo(
            opponent_id, new_opponent_elo, opponent.battle_count + 1
        )

        rating = Rating(
            voter_id=voter_id,
            challenger_type=challenger_type,
            challenger_id=challenger_id,
            opponent_type=opponent_type,
            opponent_id=opponent_id,
            winner_type=winner_type,
            winner_id=winner_id,
            challenger_elo_before=challenger.elo_score,
            opponent_elo_before=opponent.elo_score,
            challenger_elo_delta=challenger_delta,
            opponent_elo_delta=opponent_delta,
        )
        self._session.add(rating)
        await self._session.commit()

        return rating