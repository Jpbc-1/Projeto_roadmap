from datetime import date
from typing import List, Optional, Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import (
    Mission,
    MissionExecution,
    Roadmap,
    RoadmapChapter,
    UserStats,
)


class SQLAlchemyMissionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id_with_hierarchy(self, mission_id: int) -> Optional[Mission]:
        result = await self.session.execute(
            select(Mission)
            .options(
                selectinload(Mission.chapter)
                .selectinload(RoadmapChapter.roadmap)
                .selectinload(Roadmap.goal)
            )
            .where(Mission.id == mission_id)
        )
        return result.scalar_one_or_none()

    async def has_execution(self, mission_id: int, user_id: int) -> bool:
        result = await self.session.execute(
            select(MissionExecution.id).where(
                MissionExecution.mission_id == mission_id,
                MissionExecution.user_id == user_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_mission_ids_in_chapter(self, chapter_id: int) -> List[int]:
        result = await self.session.execute(select(Mission.id).where(Mission.chapter_id == chapter_id))
        return [row[0] for row in result.all()]

    async def get_completed_mission_ids(self, mission_ids: List[int], user_id: int) -> Set[int]:
        if not mission_ids:
            return set()
        result = await self.session.execute(
            select(MissionExecution.mission_id).where(
                MissionExecution.mission_id.in_(mission_ids),
                MissionExecution.user_id == user_id,
            )
        )
        return {row[0] for row in result.all()}

    async def get_next_chapter_id(self, roadmap_id: int, current_order_index: int) -> Optional[int]:
        result = await self.session.execute(
            select(RoadmapChapter.id).where(
                RoadmapChapter.roadmap_id == roadmap_id,
                RoadmapChapter.order_index == current_order_index + 1,
            )
        )
        return result.scalar_one_or_none()

    async def get_user_stats(self, user_id: int) -> Optional[UserStats]:
        result = await self.session.execute(select(UserStats).where(UserStats.user_id == user_id))
        return result.scalar_one_or_none()

    async def persist_completion(
        self,
        mission_id: int,
        user_id: int,
        xp_rewarded: int,
        user_reflection: Optional[str],
        chapter_id_to_complete: Optional[int],
        next_chapter_id_to_unlock: Optional[int],
        new_total_xp: int,
        new_level: int,
        new_current_streak: int,
        new_max_streak: int,
        activity_date: date,
    ) -> MissionExecution:
        execution = MissionExecution(
            mission_id=mission_id,
            user_id=user_id,
            xp_rewarded=xp_rewarded,
            user_reflection=user_reflection,
        )
        self.session.add(execution)

        if chapter_id_to_complete is not None:
            chapter = await self.session.get(RoadmapChapter, chapter_id_to_complete)
            if chapter is not None:
                chapter.status = "completed"

        if next_chapter_id_to_unlock is not None:
            next_chapter = await self.session.get(RoadmapChapter, next_chapter_id_to_unlock)
            if next_chapter is not None and next_chapter.status == "locked":
                next_chapter.status = "in_progress"

        stats = await self.get_user_stats(user_id)
        if stats is None:
            stats = UserStats(
                user_id=user_id,
                total_xp=new_total_xp,
                current_level=new_level,
                current_streak=new_current_streak,
                max_streak=new_max_streak,
                last_activity_date=activity_date,
            )
            self.session.add(stats)
        else:
            stats.total_xp = new_total_xp
            stats.current_level = new_level
            stats.current_streak = new_current_streak
            stats.max_streak = new_max_streak
            stats.last_activity_date = activity_date

        # Um único commit no final -> ou tudo isso é gravado junto, ou nada é.
        await self.session.commit()
        await self.session.refresh(execution)
        return execution