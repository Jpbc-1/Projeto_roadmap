from typing import List, Optional, Tuple

from app.domain.repositories.knowledge_node_repository import KnowledgeNodeRepository
from app.infrastructure.database.models import KnowledgeNode


class GetDueReviewsUseCase:
    def __init__(self, knowledge_node_repository: KnowledgeNodeRepository):
        self.knowledge_node_repository = knowledge_node_repository

    async def execute(self, user_id: int, user_timezone: str) -> List[Tuple[KnowledgeNode, Optional[str]]]:
        from datetime import date, datetime
        from zoneinfo import ZoneInfo

        try:
            today_for_user = datetime.now(ZoneInfo(user_timezone)).date()
        except Exception:
            today_for_user = date.today()

        return await self.knowledge_node_repository.get_due_for_user(user_id, today_for_user)