from datetime import date, datetime
from typing import Any, List, Optional

from sqlalchemy import Select, delete as sql_delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.flashcard_repository import FlashcardContext
from app.infrastructure.database.models import (
    Deck,
    Flashcard,
    FlashcardReview,
    Goal,
    KnowledgeNode,
    Mission,
    RoadmapChapter,
    UserStats,
)


class SQLAlchemyFlashcardRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _context_query(self) -> Select:
        """Base de toda query que precisa devolver FlashcardContext --
        LEFT OUTER JOIN em tudo depois de Deck porque um flashcard
        manual (sem knowledge_node_id) não tem missão/capítulo/goal de
        origem, e mesmo um extraído pode ter mission_id NULL (ver
        docstring de FlashcardContext)."""
        return (
            select(Flashcard, Deck.name, Mission.title, RoadmapChapter.title, Goal.id, Goal.title)
            .join(Deck, Deck.id == Flashcard.deck_id)
            .outerjoin(KnowledgeNode, KnowledgeNode.id == Flashcard.knowledge_node_id)
            .outerjoin(Mission, Mission.id == KnowledgeNode.mission_id)
            .outerjoin(RoadmapChapter, RoadmapChapter.id == Mission.chapter_id)
            .outerjoin(Goal, Goal.id == KnowledgeNode.goal_id)
        )

    @staticmethod
    def _to_context(row) -> FlashcardContext:
        flashcard, deck_name, mission_title, chapter_title, goal_id, goal_title = row
        return FlashcardContext(
            flashcard=flashcard,
            deck_name=deck_name,
            mission_title=mission_title,
            chapter_title=chapter_title,
            goal_id=goal_id,
            goal_title=goal_title,
        )

    async def create(self, **fields: Any) -> Flashcard:
        flashcard = Flashcard(**fields)
        self.session.add(flashcard)
        await self.session.commit()
        await self.session.refresh(flashcard)
        return flashcard

    async def get_by_id(self, flashcard_id: int) -> Optional[Flashcard]:
        return await self.session.get(Flashcard, flashcard_id)

    async def update(self, flashcard_id: int, **fields: Any) -> Flashcard:
        flashcard = await self.session.get(Flashcard, flashcard_id)
        if flashcard is None:
            raise ValueError(f"Flashcard {flashcard_id} não encontrado.")
        for key, value in fields.items():
            setattr(flashcard, key, value)
        await self.session.commit()
        await self.session.refresh(flashcard)
        return flashcard

    async def delete(self, flashcard_id: int) -> None:
        flashcard = await self.session.get(Flashcard, flashcard_id)
        if flashcard is None:
            return
        await self.session.execute(sql_delete(FlashcardReview).where(FlashcardReview.flashcard_id == flashcard_id))
        await self.session.delete(flashcard)
        await self.session.commit()

    async def list_pending_for_user(self, user_id: int, limit: int, offset: int) -> List[FlashcardContext]:
        query = (
            self._context_query()
            .where(Flashcard.user_id == user_id, Flashcard.status == "pending_review")
            .order_by(Flashcard.created_at, Flashcard.id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return [self._to_context(row) for row in result.all()]

    async def list_by_deck(self, deck_id: int, limit: int, offset: int) -> List[FlashcardContext]:
        query = (
            self._context_query()
            .where(Flashcard.deck_id == deck_id)
            .order_by(Flashcard.created_at, Flashcard.id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return [self._to_context(row) for row in result.all()]

    async def list_due(
        self,
        user_id: int,
        now: datetime,
        deck_id: Optional[int],
        goal_id: Optional[int],
        limit: int,
        offset: int,
    ) -> List[FlashcardContext]:
        query = self._context_query().where(
            Flashcard.user_id == user_id, Flashcard.status == "active", Flashcard.due <= now
        )
        if deck_id is not None:
            query = query.where(Flashcard.deck_id == deck_id)
        if goal_id is not None:
            query = query.where(KnowledgeNode.goal_id == goal_id)
        query = query.order_by(Flashcard.due, Flashcard.id).limit(limit).offset(offset)

        result = await self.session.execute(query)
        return [self._to_context(row) for row in result.all()]

    async def count_due(self, user_id: int, now: datetime, deck_id: Optional[int]) -> int:
        query = (
            select(func.count())
            .select_from(Flashcard)
            .where(Flashcard.user_id == user_id, Flashcard.status == "active", Flashcard.due <= now)
        )
        if deck_id is not None:
            query = query.where(Flashcard.deck_id == deck_id)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def count_reviews_since(self, user_id: int, deck_id: Optional[int], since: datetime) -> int:
        query = (
            select(func.count())
            .select_from(FlashcardReview)
            .join(Flashcard, Flashcard.id == FlashcardReview.flashcard_id)
            .where(Flashcard.user_id == user_id, FlashcardReview.reviewed_at >= since)
        )
        if deck_id is not None:
            query = query.where(Flashcard.deck_id == deck_id)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def create_review_log(
        self,
        flashcard_id: int,
        rating: str,
        old_stability: Optional[float],
        new_stability: Optional[float],
        old_difficulty: Optional[float],
        new_difficulty: Optional[float],
        elapsed_days: Optional[int],
    ) -> None:
        self.session.add(
            FlashcardReview(
                flashcard_id=flashcard_id,
                rating=rating,
                old_stability=old_stability,
                new_stability=new_stability,
                old_difficulty=old_difficulty,
                new_difficulty=new_difficulty,
                elapsed_days=elapsed_days,
            )
        )
        await self.session.commit()

    async def record_review(
        self,
        flashcard_id: int,
        rating: str,
        old_stability: Optional[float],
        new_stability: Optional[float],
        old_difficulty: Optional[float],
        new_difficulty: Optional[float],
        elapsed_days: Optional[int],
        card_updates: dict,
    ) -> Flashcard:
        flashcard = await self.session.get(Flashcard, flashcard_id)
        if flashcard is None:
            raise ValueError(f"Flashcard {flashcard_id} não encontrado.")

        for key, value in card_updates.items():
            setattr(flashcard, key, value)

        self.session.add(
            FlashcardReview(
                flashcard_id=flashcard_id,
                rating=rating,
                old_stability=old_stability,
                new_stability=new_stability,
                old_difficulty=old_difficulty,
                new_difficulty=new_difficulty,
                elapsed_days=elapsed_days,
            )
        )

        await self.session.commit()
        await self.session.refresh(flashcard)
        return flashcard

    async def get_user_stats(self, user_id: int) -> Optional[UserStats]:
        result = await self.session.execute(select(UserStats).where(UserStats.user_id == user_id))
        return result.scalar_one_or_none()

    async def apply_daily_review_bonus(
        self,
        user_id: int,
        total_xp: int,
        level: int,
        current_streak: int,
        max_streak: int,
        activity_date: date,
    ) -> bool:
        result = await self.session.execute(
            update(UserStats)
            .where(
                UserStats.user_id == user_id,
                (UserStats.last_bonus_date.is_(None)) | (UserStats.last_bonus_date < activity_date),
            )
            .values(
                total_xp=total_xp,
                current_level=level,
                current_streak=current_streak,
                max_streak=max_streak,
                last_activity_date=activity_date,
                last_bonus_date=activity_date,
            )
        )
        if result.rowcount > 0:
            await self.session.commit()
            return True

        await self.session.rollback()

        stats = await self.get_user_stats(user_id)
        if stats is not None:
            return False

        stats = UserStats(
            user_id=user_id,
            total_xp=total_xp,
            current_level=level,
            current_streak=current_streak,
            max_streak=max_streak,
            last_activity_date=activity_date,
            last_bonus_date=activity_date,
        )
        self.session.add(stats)
        await self.session.commit()
        return True
