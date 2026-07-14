from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import Mission, Roadmap, RoadmapChapter


class SQLAlchemyRoadmapRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_full_roadmap(
        self,
        goal_id: int,
        version: int,
        ai_generation_log: Dict[str, Any],
        chapters_data: List[Dict[str, Any]],
    ) -> Roadmap:
        roadmap = Roadmap(
            goal_id=goal_id,
            version=version,
            is_active=True,
            ai_generation_log=ai_generation_log,
        )
        self.session.add(roadmap)
        await self.session.flush()

        for chapter_index, chapter_data in enumerate(chapters_data):
            chapter = RoadmapChapter(
                roadmap_id=roadmap.id,
                title=chapter_data["title"],
                order_index=chapter_index,
                status="in_progress" if chapter_index == 0 else "locked",
            )
            self.session.add(chapter)
            await self.session.flush()

            for mission_index, mission_data in enumerate(chapter_data.get("missions", [])):
                mission = Mission(
                    chapter_id=chapter.id,
                    title=mission_data["title"],
                    description=mission_data.get("description"),
                    estimated_minutes=mission_data.get("estimated_minutes"),
                    order_index=mission_index,
                )
                self.session.add(mission)

        await self.session.commit()
        await self.session.refresh(roadmap)
        return roadmap

    async def get_active_by_goal(self, goal_id: int) -> Optional[Roadmap]:
        result = await self.session.execute(
            select(Roadmap)
            .options(selectinload(Roadmap.chapters).selectinload(RoadmapChapter.missions))
            .where(Roadmap.goal_id == goal_id, Roadmap.is_active.is_(True))
        )
        return result.scalar_one_or_none()