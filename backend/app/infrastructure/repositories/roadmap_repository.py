from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import Goal, Mission, MissionExecution, Roadmap, RoadmapChapter


def _coerce_bool(value: Any, default: bool) -> bool:
    """A geração de capítulos/missões (create_full_roadmap, _insert_chapters,
    split_chapter_with_new) não usa response_schema do Gemini -- então
    'is_conceptual' vem só por instrução de prompt, sem validação de tipo
    garantida pela API. Isso evita o typo clássico de tratar a STRING "false"
    como truthy (bool("false") é True em Python) se a IA ocasionalmente
    devolver texto em vez de um boolean de verdade."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes")
    return default


def _coerce_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """Mesma razão do _coerce_bool acima: sem response_schema, nada garante
    que 'estimated_minutes' venha como int de verdade -- a IA já devolveu
    isso como string ocasionalmente (ex: "20 minutos" em vez de 20), o que
    quebra o INSERT no meio da transação (erro de tipo no Postgres) e, sem
    tratamento, deixa o Goal preso em "pending" para sempre (ver rollback
    em generate_roadmap.py)."""
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        digits = "".join(ch for ch in value if ch.isdigit())
        if digits:
            return int(digits)
    return default


def _mission_from_ai_data(chapter_id: int, order_index: int, data: Dict[str, Any]) -> Mission:
    """Constrói um Mission a partir do dict que vem da IA, com a MESMA
    coerção de tipo em todo lugar que cria missão gerada por IA -- extraído
    porque esse bloco existia quase idêntico em 5 métodos diferentes
    (create_full_roadmap, _insert_chapters, split_chapter_with_new,
    replace_chapter_content, insert_full_chapter_after): corrigir um tipo
    aqui precisava ser lembrado em 5 lugares, fácil de esquecer um."""
    return Mission(
        chapter_id=chapter_id,
        title=data["title"],
        description=data.get("description"),
        estimated_minutes=_coerce_int(data.get("estimated_minutes")),
        order_index=order_index,
        is_conceptual=_coerce_bool(data.get("is_conceptual"), default=True),
        created_by="ai",
    )


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
                created_by="ai",
            )
            self.session.add(chapter)
            await self.session.flush()

            for mission_index, mission_data in enumerate(chapter_data.get("missions", [])):
                self.session.add(_mission_from_ai_data(chapter.id, mission_index, mission_data))

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
                created_by="ai",
            )
            self.session.add(chapter)
            await self.session.flush()

            for mission_index, mission_data in enumerate(chapter_data.get("missions", [])):
                self.session.add(_mission_from_ai_data(chapter.id, mission_index, mission_data))

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

    async def insert_chapter_after(
        self,
        roadmap_id: int,
        title: str,
        after_order_index: int,
        status: str,
    ) -> RoadmapChapter:
        target_order_index = after_order_index + 1

        result = await self.session.execute(
            select(RoadmapChapter)
            .where(
                RoadmapChapter.roadmap_id == roadmap_id,
                RoadmapChapter.order_index >= target_order_index,
            )
            .order_by(RoadmapChapter.order_index.desc())
        )
        for chapter_to_shift in result.scalars().all():
            chapter_to_shift.order_index += 1

        new_chapter = RoadmapChapter(
            roadmap_id=roadmap_id,
            title=title,
            order_index=target_order_index,
            status=status,
            created_by="user",
        )
        self.session.add(new_chapter)
        await self.session.commit()
        await self.session.refresh(new_chapter)
        return new_chapter

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
    ) -> List[Dict[str, Any]]:
        conditions = [
            Mission.chapter_id == chapter_id,
            MissionExecution.user_id == user_id,
            or_(
                MissionExecution.user_reflection.is_not(None),
                MissionExecution.difficulty_rating.is_not(None),
                MissionExecution.satisfaction_rating.is_not(None),
            ),
        ]
        if since is not None:
            conditions.append(MissionExecution.completed_at > since)

        result = await self.session.execute(
            select(
                Mission.title,
                MissionExecution.user_reflection,
                MissionExecution.difficulty_rating,
                MissionExecution.satisfaction_rating,
            )
            .join(MissionExecution, MissionExecution.mission_id == Mission.id)
            .where(*conditions)
        )
        return [
            {
                "mission_title": title,
                "reflection": reflection,
                "difficulty_rating": difficulty_rating,
                "satisfaction_rating": satisfaction_rating,
            }
            for title, reflection, difficulty_rating, satisfaction_rating in result.all()
        ]

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
            old_chapter.closed_early = True

        new_chapter = RoadmapChapter(
            roadmap_id=roadmap_id,
            title=new_chapter_title,
            order_index=new_chapter_order_index,
            status="in_progress",  
            created_by="ai",
        )
        self.session.add(new_chapter)
        await self.session.flush()

        for offset, mission_data in enumerate(new_chapter_missions):
            self.session.add(_mission_from_ai_data(new_chapter.id, offset, mission_data))

        await self.session.commit()

    async def count_completed_chapters(self, roadmap_id: int) -> int:
        result = await self.session.execute(
            select(RoadmapChapter.id).where(
                RoadmapChapter.roadmap_id == roadmap_id,
                RoadmapChapter.status == "completed",
                RoadmapChapter.closed_early.is_(False),
            )
        )
        return len(result.all())

    async def get_reflections_for_chapters(
        self, chapter_ids: List[int], user_id: int
    ) -> List[Dict[str, Any]]:
        if not chapter_ids:
            return []
        result = await self.session.execute(
            select(
                Mission.title,
                MissionExecution.user_reflection,
                MissionExecution.difficulty_rating,
                MissionExecution.satisfaction_rating,
            )
            .join(MissionExecution, MissionExecution.mission_id == Mission.id)
            .where(
                Mission.chapter_id.in_(chapter_ids),
                MissionExecution.user_id == user_id,
                or_(
                    MissionExecution.user_reflection.is_not(None),
                    MissionExecution.difficulty_rating.is_not(None),
                    MissionExecution.satisfaction_rating.is_not(None),
                ),
            )
        )
        return [
            {
                "mission_title": title,
                "reflection": reflection,
                "difficulty_rating": difficulty_rating,
                "satisfaction_rating": satisfaction_rating,
            }
            for title, reflection, difficulty_rating, satisfaction_rating in result.all()
        ]

    async def get_chapters_by_roadmap(self, roadmap_id: int) -> List[RoadmapChapter]:
        result = await self.session.execute(
            select(RoadmapChapter).where(RoadmapChapter.roadmap_id == roadmap_id)
        )
        return list(result.scalars().all())

    async def get_missions_by_chapter(self, chapter_id: int) -> List[Mission]:
        result = await self.session.execute(select(Mission).where(Mission.chapter_id == chapter_id))
        return list(result.scalars().all())

    async def add_mission_to_chapter(
        self,
        chapter_id: int,
        title: str,
        description: Optional[str],
        estimated_minutes: Optional[int],
    ) -> Mission:
        existing_result = await self.session.execute(
            select(Mission.order_index).where(Mission.chapter_id == chapter_id)
        )
        existing_indexes = [row[0] for row in existing_result.all()]
        next_order_index = (max(existing_indexes) + 1) if existing_indexes else 0

        mission = Mission(
            chapter_id=chapter_id,
            title=title,
            description=description,
            estimated_minutes=estimated_minutes,
            order_index=next_order_index,
            is_conceptual=True,
            created_by="user",
        )
        self.session.add(mission)
        await self.session.commit()
        await self.session.refresh(mission)
        return mission

    async def update_mission(self, mission_id: int, **fields: Any) -> Mission:
        mission = await self.session.get(Mission, mission_id)
        if mission is None:
            raise ValueError(f"Mission {mission_id} não encontrada para atualização.")

        for field_name, value in fields.items():
            setattr(mission, field_name, value)

        await self.session.commit()
        await self.session.refresh(mission)
        return mission

    async def delete_mission(self, mission_id: int) -> None:
        mission = await self.session.get(Mission, mission_id)
        if mission is None:
            return
        chapter_id = mission.chapter_id

        await self.session.execute(delete(Mission).where(Mission.id == mission_id))

        result = await self.session.execute(
            select(Mission).where(Mission.chapter_id == chapter_id).order_by(Mission.order_index)
        )
        for new_index, remaining_mission in enumerate(result.scalars().all()):
            if remaining_mission.order_index != new_index:
                remaining_mission.order_index = new_index

        await self.session.commit()

    async def complete_chapter_and_unlock_next(self, chapter_id: int, next_chapter_id: Optional[int]) -> None:
        chapter = await self.session.get(RoadmapChapter, chapter_id)
        if chapter is not None:
            chapter.status = "completed"

        if next_chapter_id is not None:
            next_chapter = await self.session.get(RoadmapChapter, next_chapter_id)
            if next_chapter is not None and next_chapter.status == "locked":
                next_chapter.status = "in_progress"

        await self.session.commit()

    async def set_pending_adaptation(self, roadmap_id: int, operation: Dict[str, Any]) -> None:
        roadmap = await self.session.get(Roadmap, roadmap_id)
        if roadmap is not None:
            roadmap.pending_adaptation = operation
            await self.session.commit()

    async def clear_pending_adaptation(self, roadmap_id: int) -> None:
        roadmap = await self.session.get(Roadmap, roadmap_id)
        if roadmap is not None:
            roadmap.pending_adaptation = None
            await self.session.commit()

    async def replace_chapter_content(
        self, chapter_id: int, title: str, missions_data: List[Dict[str, Any]]
    ) -> None:
        chapter = await self.session.get(RoadmapChapter, chapter_id)
        if chapter is None:
            return

        result = await self.session.execute(
            select(Mission.id)
            .outerjoin(MissionExecution, MissionExecution.mission_id == Mission.id)
            .where(Mission.chapter_id == chapter_id, MissionExecution.id.is_(None))
        )
        mission_ids_to_delete = [row[0] for row in result.all()]
        if mission_ids_to_delete:
            await self.session.execute(delete(Mission).where(Mission.id.in_(mission_ids_to_delete)))

        chapter.title = title

        result = await self.session.execute(
            select(func.max(Mission.order_index)).where(Mission.chapter_id == chapter_id)
        )
        next_order_index = (result.scalar() or -1) + 1

        for offset, mission_data in enumerate(missions_data):
            self.session.add(_mission_from_ai_data(chapter_id, next_order_index + offset, mission_data))

        await self.session.commit()

    async def insert_full_chapter_after(
        self,
        roadmap_id: int,
        after_order_index: int,
        title: str,
        missions_data: List[Dict[str, Any]],
        status: str = "locked",
    ) -> RoadmapChapter:
        target_order_index = after_order_index + 1

        result = await self.session.execute(
            select(RoadmapChapter)
            .where(
                RoadmapChapter.roadmap_id == roadmap_id,
                RoadmapChapter.order_index >= target_order_index,
            )
            .order_by(RoadmapChapter.order_index.desc())
        )
        for chapter_to_shift in result.scalars().all():
            chapter_to_shift.order_index += 1

        new_chapter = RoadmapChapter(
            roadmap_id=roadmap_id,
            title=title,
            order_index=target_order_index,
            status=status,
            created_by="ai",
        )
        self.session.add(new_chapter)
        await self.session.flush()

        for offset, mission_data in enumerate(missions_data):
            self.session.add(_mission_from_ai_data(new_chapter.id, offset, mission_data))

        await self.session.commit()
        await self.session.refresh(new_chapter)
        return new_chapter

    async def set_chapter_lock(self, chapter_id: int, locked: bool) -> None:
        chapter = await self.session.get(RoadmapChapter, chapter_id)
        if chapter is not None:
            chapter.is_locked_from_ai = locked
            await self.session.commit()

    async def get_current_pending_mission_title_for_user(self, user_id: int) -> Optional[str]:
        result = await self.session.execute(
            select(Roadmap)
            .join(Goal, Goal.id == Roadmap.goal_id)
            .where(Goal.user_id == user_id, Roadmap.is_active.is_(True))
            .options(selectinload(Roadmap.chapters).selectinload(RoadmapChapter.missions))
            .order_by(Goal.created_at.desc())
        )
        roadmaps = list(result.scalars().unique().all())
        if not roadmaps:
            return None

        current_chapter = next((c for c in roadmaps[0].chapters if c.status == "in_progress"), None)
        if current_chapter is None or not current_chapter.missions:
            return None

        mission_ids = [m.id for m in current_chapter.missions]
        result = await self.session.execute(
            select(MissionExecution.mission_id).where(
                MissionExecution.mission_id.in_(mission_ids), MissionExecution.user_id == user_id
            )
        )
        completed_ids = {row[0] for row in result.all()}

        next_mission = next((m for m in current_chapter.missions if m.id not in completed_ids), None)
        return next_mission.title if next_mission else None