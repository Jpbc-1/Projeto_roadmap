from dataclasses import dataclass
from datetime import date, timedelta

from app.application.goals.get_goal import GoalAccessDeniedError, GoalNotFoundError
from app.application.knowledge.embedding_utils import find_duplicate_node
from app.core.ai.gemini_client import GeminiClient
from app.domain.repositories.goal_repository import GoalRepository
from app.domain.repositories.knowledge_node_repository import KnowledgeNodeRepository
from app.infrastructure.database.models import KnowledgeNode


@dataclass
class CreateKnowledgeNodeResult:
    node: KnowledgeNode
    was_duplicate: bool 


class CreateKnowledgeNodeUseCase:
    def __init__(
        self,
        goal_repository: GoalRepository,
        knowledge_node_repository: KnowledgeNodeRepository,
        embedding_ai_client: GeminiClient,
    ):
        self.goal_repository = goal_repository
        self.knowledge_node_repository = knowledge_node_repository
        self.embedding_ai_client = embedding_ai_client

    async def execute(self, goal_id: int, user_id: int, topic_name: str) -> CreateKnowledgeNodeResult:
        goal = await self.goal_repository.get_by_id(goal_id)
        if goal is None:
            raise GoalNotFoundError(f"Objetivo {goal_id} não encontrado.")
        if goal.user_id != user_id:
            raise GoalAccessDeniedError("Você não tem acesso a este objetivo.")

        clean_topic_name = topic_name.strip()
        embedding = await self.embedding_ai_client.embed_text(clean_topic_name)

        existing_nodes = await self.knowledge_node_repository.get_by_goal(goal_id)
        duplicate = find_duplicate_node(embedding, existing_nodes)
        if duplicate is not None:
            return CreateKnowledgeNodeResult(node=duplicate, was_duplicate=True)

        node = await self.knowledge_node_repository.create(
            goal_id=goal_id,
            user_id=user_id,
            topic_name=clean_topic_name,
            embedding=embedding,
            next_review_date=date.today() + timedelta(days=1),
        )
        return CreateKnowledgeNodeResult(node=node, was_duplicate=False)