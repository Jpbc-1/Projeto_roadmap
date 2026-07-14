from app.domain.repositories.goal_repository import GoalRepository
from app.infrastructure.database.models import Goal


class GoalNotFoundError(Exception):
    """Levantado quando o goal não existe no banco."""


class GoalAccessDeniedError(Exception):
    """Levantado quando o goal existe, mas pertence a outro usuário."""


class GetGoalUseCase:
    def __init__(self, goal_repository: GoalRepository):
        self.goal_repository = goal_repository

    async def execute(self, goal_id: int, user_id: int) -> Goal:
        goal = await self.goal_repository.get_by_id(goal_id)

        if goal is None:
            raise GoalNotFoundError(f"Objetivo {goal_id} não encontrado.")

        if goal.user_id != user_id:
            raise GoalAccessDeniedError("Você não tem acesso a este objetivo.")

        return goal