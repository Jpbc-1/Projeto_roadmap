from typing import List, Optional

from pydantic import BaseModel, Field


class MissionProgressOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    estimated_minutes: Optional[int]
    order_index: int
    completed: bool
    is_conceptual: bool
    created_by: str


class ChapterProgressOut(BaseModel):
    id: int
    title: str
    order_index: int
    status: str 
    created_by: str
    is_locked_from_ai: bool
    missions: List[MissionProgressOut]


class RoadmapProgressOut(BaseModel):
    id: int
    version: int
    # Calculados no backend (primeiro capítulo "in_progress" e, dentro dele,
    # a primeira missão ainda não concluída) -- assim o front não precisa
    # varrer chapters/missions pra descobrir "o que vem agora". None quando
    # o roadmap inteiro já foi concluído.
    current_chapter_id: Optional[int]
    current_mission_id: Optional[int]
    chapters: List[ChapterProgressOut]


class AdaptGoalRequest(BaseModel):
    feedback: Optional[str] = None


class ChapterCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    # Se informado, o capítulo entra logo após esse (em qualquer posição do
    # roadmap). Se omitido, entra no final -- mesmo comportamento de antes.
    after_chapter_id: Optional[int] = None


class AdaptGoalResponse(BaseModel):
    message: str
    # True quando o feedback mirou um capítulo específico: a operação foi
    # gerada mas NÃO aplicada ainda -- o front deve mostrar "message" (o
    # resumo da mudança) e chamar /adapt/confirm ou /adapt/reject.
    # False = já foi aplicado direto, do jeito que sempre funcionou
    # (feedback amplo, sobre ritmo/dificuldade geral).
    requires_confirmation: bool = False
    # Antes disso era um único "new_chapters_count" que somava capítulo e
    # missão juntos (bug -- o número não representava nem um nem outro).
    # Separados, cada um na sua unidade de verdade.
    chapters_changed: Optional[int] = None
    missions_changed: Optional[int] = None


class ChapterLockRequest(BaseModel):
    locked: bool