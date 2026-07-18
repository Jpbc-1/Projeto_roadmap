from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import Mission, MissionExecution, Roadmap, RoadmapChapter


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

    async def get_chapter_ids_with_executions(self, chapter_ids: List[int]) -> Set[int]:
        """Checagem de segurança: quais desses capítulos têm QUALQUER missão
        já executada -- esses NUNCA podem ser apagados, mesmo que estejam
        marcados como 'locked' (não deveria acontecer, mas não confiamos
        cegamente só no status)."""
        if not chapter_ids:
            return set()
        result = await self.session.execute(
            select(Mission.chapter_id)
            .join(MissionExecution, MissionExecution.mission_id == Mission.id)
            .where(Mission.chapter_id.in_(chapter_ids))
            .distinct()
        )
        return {row[0] for row in result.all()}

    async def _insert_chapters(
        self,
        roadmap_id: int,
        chapters_data: List[Dict[str, Any]],
        starting_order_index: int,
        first_chapter_status: str,
    ) -> None:
        for offset, chapter_data in enumerate(chapters_data):
            chapter = RoadmapChapter(
                roadmap_id=roadmap_id,
                title=chapter_data["title"],
                order_index=starting_order_index + offset,
                status=first_chapter_status if offset == 0 else "locked",
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

    async def _bump_version(self, roadmap_id: int, ai_generation_log: Dict[str, Any]) -> None:
        roadmap = await self.session.get(Roadmap, roadmap_id)
        if roadmap is not None:
            roadmap.version += 1
            roadmap.ai_generation_log = ai_generation_log
            roadmap.last_adapted_at = datetime.now(timezone.utc)

    async def append_chapters(
        self,
        roadmap_id: int,
        chapters_data: List[Dict[str, Any]],
        starting_order_index: int,
        unlock_first_chapter: bool,
        ai_generation_log: Dict[str, Any],
    ) -> None:
        """Modo ESTENDER: usado quando não sobra nenhum capítulo 'locked'
        -- adiciona uma leva nova no final do roadmap."""
        await self._insert_chapters(
            roadmap_id=roadmap_id,
            chapters_data=chapters_data,
            starting_order_index=starting_order_index,
            first_chapter_status="in_progress" if unlock_first_chapter else "locked",
        )
        await self._bump_version(roadmap_id, ai_generation_log)
        await self.session.commit()

    async def replace_locked_chapters(
        self,
        roadmap_id: int,
        chapter_ids_to_delete: List[int],
        chapters_data: List[Dict[str, Any]],
        starting_order_index: int,
        ai_generation_log: Dict[str, Any],
    ) -> None:
        """Modo REESCREVER: usado quando ainda existem capítulos 'locked'
        pendentes -- apaga esses capítulos (nunca começados, sem nenhuma
        missão executada) e insere os novos no lugar deles, evitando
        duplicação de conteúdo."""
        if chapter_ids_to_delete:
            await self.session.execute(delete(Mission).where(Mission.chapter_id.in_(chapter_ids_to_delete)))
            await self.session.execute(
                delete(RoadmapChapter).where(RoadmapChapter.id.in_(chapter_ids_to_delete))
            )

        await self._insert_chapters(
            roadmap_id=roadmap_id,
            chapters_data=chapters_data,
            starting_order_index=starting_order_index,
            first_chapter_status="locked",
        )
        await self._bump_version(roadmap_id, ai_generation_log)
        await self.session.commit()

    async def get_pending_mission_ids(self, chapter_id: int, user_id: int) -> List[int]:
        result = await self.session.execute(
            select(Mission.id)
            .outerjoin(
                MissionExecution,
                (MissionExecution.mission_id == Mission.id) & (MissionExecution.user_id == user_id),
            )
            .where(Mission.chapter_id == chapter_id, MissionExecution.id.is_(None))
        )
        return [row[0] for row in result.all()]

    async def get_chapter_reflections(
        self, chapter_id: int, user_id: int, since: Optional[datetime] = None
    ) -> List[Dict[str, str]]:
        conditions = [
            Mission.chapter_id == chapter_id,
            MissionExecution.user_id == user_id,
            MissionExecution.user_reflection.is_not(None),
        ]
        if since is not None:
            conditions.append(MissionExecution.completed_at > since)

        result = await self.session.execute(
            select(Mission.title, MissionExecution.user_reflection)
            .join(MissionExecution, MissionExecution.mission_id == Mission.id)
            .where(*conditions)
        )
        return [{"mission_title": title, "reflection": reflection} for title, reflection in result.all()]

    async def split_chapter_with_new(
        self,
        roadmap_id: int,
        chapter_id: int,
        mission_ids_to_delete: List[int],
        new_chapter_title: str,
        new_chapter_order_index: int,
        new_chapter_missions: List[Dict[str, Any]],
    ) -> None:
        if mission_ids_to_delete:
            await self.session.execute(delete(Mission).where(Mission.id.in_(mission_ids_to_delete)))

        old_chapter = await self.session.get(RoadmapChapter, chapter_id)
        if old_chapter is not None:
            old_chapter.status = "completed"

        new_chapter = RoadmapChapter(
            roadmap_id=roadmap_id,
            title=new_chapter_title,
            order_index=new_chapter_order_index,
            status="in_progress",  # já é o capítulo ativo -- segue direto do que fechou agora
        )
        self.session.add(new_chapter)
        await self.session.flush()

        for offset, mission_data in enumerate(new_chapter_missions):
            mission = Mission(
                chapter_id=new_chapter.id,
                title=mission_data["title"],
                description=mission_data.get("description"),
                estimated_minutes=mission_data.get("estimated_minutes"),
                order_index=offset,
            )
            self.session.add(mission)

        await self.session.commit()

    async def count_completed_chapters(self, roadmap_id: int) -> int:
        result = await self.session.execute(
            select(RoadmapChapter.id).where(
                RoadmapChapter.roadmap_id == roadmap_id,
                RoadmapChapter.status == "completed",
            )
        )
        return len(result.all())

    async def get_reflections_for_chapters(
        self, chapter_ids: List[int], user_id: int
    ) -> List[Dict[str, str]]:
        if not chapter_ids:
            return []
        result = await self.session.execute(
            select(Mission.title, MissionExecution.user_reflection)
            .join(MissionExecution, MissionExecution.mission_id == Mission.id)
            .where(
                Mission.chapter_id.in_(chapter_ids),
                MissionExecution.user_id == user_id,
                MissionExecution.user_reflection.is_not(None),
            )
        )
        return [{"mission_title": title, "reflection": reflection} for title, reflection in result.all()]

    async def get_chapters_by_roadmap(self, roadmap_id: int) -> List[RoadmapChapter]:
        result = await self.session.execute(
            select(RoadmapChapter).where(RoadmapChapter.roadmap_id == roadmap_id)
        )
        return list(result.scalars().all())