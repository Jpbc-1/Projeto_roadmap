from dataclasses import dataclass
from datetime import date, timedelta

from app.application.gamification.streak import calculate_streak_update
from app.application.knowledge.spaced_repetition import QUALITY_MAP, apply_sm2
from app.domain.repositories.knowledge_node_repository import KnowledgeNodeRepository
from app.infrastructure.database.models import KnowledgeNode

DAILY_REVIEW_BONUS_XP = 20


class KnowledgeNodeNotFoundError(Exception):
    """Levantado quando o nó de conhecimento não existe."""


class KnowledgeNodeAccessDeniedError(Exception):
    """Levantado quando o nó existe, mas pertence a outro usuário."""


@dataclass
class AnswerReviewResult:
    node: KnowledgeNode
    remaining_reviews_today: int
    daily_bonus_awarded: bool
    xp_earned: int


class AnswerReviewUseCase:
    def __init__(self, knowledge_node_repository: KnowledgeNodeRepository):
        self.knowledge_node_repository = knowledge_node_repository

    async def execute(self, node_id: int, user_id: int, difficulty: str) -> AnswerReviewResult:
        node = await self.knowledge_node_repository.get_by_id(node_id)
        if node is None:
            raise KnowledgeNodeNotFoundError(f"Conceito {node_id} não encontrado.")
        if node.user_id != user_id:
            raise KnowledgeNodeAccessDeniedError("Você não tem acesso a este conceito.")

        quality = QUALITY_MAP[difficulty]
        new_interval, new_factor, new_repetition_count = apply_sm2(
            quality=quality,
            easiness_factor=node.easiness_factor,
            interval_days=node.interval_days,
            repetition_count=node.repetition_count,
        )

        updated_node = await self.knowledge_node_repository.record_review(
            node_id=node_id,
            difficulty=difficulty,
            old_interval=node.interval_days,
            new_interval=new_interval,
            old_factor=node.easiness_factor,
            new_factor=new_factor,
            new_repetition_count=new_repetition_count,
            next_review_date=date.today() + timedelta(days=new_interval),
        )

        remaining = await self.knowledge_node_repository.get_due_for_user(user_id, date.today())
        remaining_count = len(remaining)

        daily_bonus_awarded = False
        xp_earned = 0
        if remaining_count == 0:
            await self._award_daily_bonus(user_id)
            daily_bonus_awarded = True
            xp_earned = DAILY_REVIEW_BONUS_XP

        return AnswerReviewResult(
            node=updated_node,
            remaining_reviews_today=remaining_count,
            daily_bonus_awarded=daily_bonus_awarded,
            xp_earned=xp_earned,
        )

    async def _award_daily_bonus(self, user_id: int) -> None:
        stats = await self.knowledge_node_repository.get_user_stats(user_id)
        update = calculate_streak_update(stats, xp_to_add=DAILY_REVIEW_BONUS_XP, today=date.today())

        await self.knowledge_node_repository.apply_daily_review_bonus(
            user_id=user_id,
            total_xp=update.new_total_xp,
            level=update.new_level,
            current_streak=update.new_current_streak,
            max_streak=update.new_max_streak,
            activity_date=update.activity_date,
        )