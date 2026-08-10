from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.knowledge import AnswerReviewRequest, DueReviewOut, ReviewResultOut
from app.application.knowledge.answer_review import (
    AnswerReviewUseCase,
    KnowledgeNodeAccessDeniedError,
    KnowledgeNodeNotFoundError,
)
from app.application.knowledge.get_due_reviews import GetDueReviewsUseCase
from app.application.knowledge.spaced_repetition import compute_mastery_level
from app.infrastructure.database.models import User
from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.knowledge_node_repository import SQLAlchemyKnowledgeNodeRepository

router = APIRouter()


@router.get("/due", response_model=List[DueReviewOut])
async def get_due_reviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repository = SQLAlchemyKnowledgeNodeRepository(db)
    use_case = GetDueReviewsUseCase(repository)
    items = await use_case.execute(current_user.id, current_user.timezone)

    return [
        DueReviewOut(
            node_id=node.id,
            goal_id=node.goal_id,
            goal_title=goal_title,
            topic_name=node.topic_name,
            next_review_date=node.next_review_date,
            mastery_level=compute_mastery_level(node.interval_days),
        )
        for node, goal_title in items
    ]


@router.post("/{node_id}/review", response_model=ReviewResultOut)
async def answer_review(
    node_id: int,
    payload: AnswerReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repository = SQLAlchemyKnowledgeNodeRepository(db)
    use_case = AnswerReviewUseCase(repository)

    try:
        result = await use_case.execute(
            node_id=node_id, user_id=current_user.id, difficulty=payload.difficulty,
            user_timezone=current_user.timezone,
        )
    except (KnowledgeNodeNotFoundError, KnowledgeNodeAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conceito não encontrado.")

    return ReviewResultOut(
        node_id=result.node.id,
        topic_name=result.node.topic_name,
        new_interval_days=result.node.interval_days,
        new_easiness_factor=result.node.easiness_factor,
        next_review_date=result.node.next_review_date,
        mastery_level=compute_mastery_level(result.node.interval_days),
        remaining_reviews_today=result.remaining_reviews_today,
        daily_bonus_awarded=result.daily_bonus_awarded,
        xp_earned=result.xp_earned,
    )