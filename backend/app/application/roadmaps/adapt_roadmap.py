import asyncio
from typing import Any, Dict, List, Optional

from app.application.goals.get_goal import GoalAccessDeniedError, GoalNotFoundError
from app.core.ai.gemini_client import GeminiClient
from app.domain.repositories.goal_repository import GoalRepository
from app.domain.repositories.roadmap_repository import RoadmapRepository

IMMEDIATE_SYSTEM_INSTRUCTION = """
Você é a IA do Roadmap AI. O usuário está no meio de um capítulo do roadmap
e pediu uma adaptação. O capítulo atual vai ser ENCERRADO no que já foi
concluído, e você vai criar o PRÓXIMO capítulo -- que assume imediatamente,
como o capítulo ativo agora.

Você recebe: contexto do objetivo, o que já foi coberto na jornada,
reflexões recentes do usuário sobre missões concluídas, feedback direto (se
houver), e quantas missões esse novo capítulo deve ter.

Gere um título para esse novo capítulo -- pode ser uma continuação natural
do capítulo anterior, ou pode refletir uma mudança de direção real, se o
feedback/reflexões indicarem isso claramente (não force uma virada se não
houver sinal para isso). Gere EXATAMENTE a quantidade de missões pedida.

Ajuste dificuldade e ritmo conforme os sinais recebidos: se indicarem que
está fácil/lento, torne mais denso e avance mais rápido; se indicarem
dificuldade ou cansaço, torne mais leve e inclua ao menos uma missão de
"descanso ativo" (revisão leve, sem conteúdo novo). Sem nenhum sinal,
mantenha o ritmo coerente com o que já vinha sendo usado.
"""


def _build_immediate_schema(missions_count: int) -> Dict[str, Any]:
    """Schema com minItems=maxItems=missions_count -- força a IA a devolver
    a quantidade EXATA de missões pedida. Seguro de usar aqui porque é um
    array de 1 nível só (sem array aninhado dentro de array, que foi o que
    causou o erro 'too many states for serving' na geração de capítulos)."""
    return {
        "type": "OBJECT",
        "properties": {
            "chapter_title": {"type": "STRING"},
            "missions": {
                "type": "ARRAY",
                "minItems": missions_count,
                "maxItems": missions_count,
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING"},
                        "description": {"type": "STRING"},
                        "estimated_minutes": {"type": "INTEGER"},
                    },
                    "required": ["title", "description", "estimated_minutes"],
                },
            },
        },
        "required": ["chapter_title", "missions"],
    }


CHAPTERS_SYSTEM_INSTRUCTION = """
Você é a IA do Roadmap AI. Gere a PRÓXIMA leva de capítulos da jornada do
usuário, continuando de onde ela realmente parou.

Você recebe: contexto do objetivo, o que já foi coberto (com as missões de
cada capítulo, para saber o nível de detalhe já tratado), reflexões
recentes do usuário e feedback direto (se houver).

Regras:
- NÃO repita temas, subtemas ou missões equivalentes ao que já está listado
  como coberto, mesmo com nomes diferentes.
- Leve em conta o feedback/reflexões para calibrar ritmo: fácil/lento ->
  conteúdo mais denso e progressão mais rápida; difícil/cansativo ->
  conteúdo mais leve, mais consolidação, incluindo ao menos uma missão de
  "descanso ativo". Sem sinal nenhum, mantenha o ritmo anterior.
- Gere 2 a 6 capítulos, cada um com 3 a 7 missões.

Responda SOMENTE em JSON válido, sem texto antes ou depois, neste formato:

{
  "chapters": [
    {
      "title": "string",
      "missions": [
        {"title": "string", "description": "string", "estimated_minutes": number}
      ]
    }
  ]
}
"""


class AdaptationFailedError(Exception):
    """Levantado quando a IA falha ou devolve algo em formato inválido."""


class AdaptRoadmapUseCase:
    def __init__(
        self,
        goal_repository: GoalRepository,
        roadmap_repository: RoadmapRepository,
        ai_client: GeminiClient,
    ):
        self.goal_repository = goal_repository
        self.roadmap_repository = roadmap_repository
        self.ai_client = ai_client

    async def execute(self, goal_id: int, user_id: int, feedback: Optional[str]) -> int:
        """Retorna quantos itens (capítulo imediato + capítulos futuros) foram alterados."""
        goal = await self.goal_repository.get_by_id(goal_id)
        if goal is None:
            raise GoalNotFoundError(f"Objetivo {goal_id} não encontrado.")
        if goal.user_id != user_id:
            raise GoalAccessDeniedError("Você não tem acesso a este objetivo.")

        from app.application.roadmaps.get_roadmap import RoadmapNotFoundError

        roadmap = await self.roadmap_repository.get_active_by_goal(goal_id)
        if roadmap is None or not roadmap.chapters:
            raise RoadmapNotFoundError("Nenhum roadmap ativo para este objetivo ainda.")

        current_chapter = next((c for c in roadmap.chapters if c.status == "in_progress"), None)

        pending_missions_sorted = []
        reflections: List[Dict[str, str]] = []
        if current_chapter is not None:
            pending_ids = set(
                await self.roadmap_repository.get_pending_mission_ids(current_chapter.id, user_id)
            )
            pending_missions_sorted = sorted(
                (m for m in current_chapter.missions if m.id in pending_ids),
                key=lambda m: m.order_index,
            )
            reflections = await self.roadmap_repository.get_chapter_reflections(
                current_chapter.id, user_id, since=roadmap.last_adapted_at
            )
        else:
            last_completed = max(
                (c for c in roadmap.chapters if c.status == "completed"),
                key=lambda c: c.order_index,
                default=None,
            )
            if last_completed is not None:
                reflections = await self.roadmap_repository.get_chapter_reflections(
                    last_completed.id, user_id, since=roadmap.last_adapted_at
                )

        locked_chapters = [c for c in roadmap.chapters if c.status == "locked"]
        safe_locked_ids = (
            await self._filter_safely_deletable(locked_chapters) if locked_chapters else []
        )
        context_chapters = [c for c in roadmap.chapters if c.id not in safe_locked_ids]

        immediate_task = self._generate_immediate_chapter(
            goal, reflections, feedback, len(pending_missions_sorted)
        )
        chapters_task = self._generate_chapters(goal, context_chapters, feedback, reflections)
        immediate_result, chapters_data = await asyncio.gather(immediate_task, chapters_task)

        changed_count = 0
        next_starting_order_index = roadmap.chapters[-1].order_index + 1
        unlock_next_leva_immediately = roadmap.chapters[-1].status == "completed"

        if pending_missions_sorted and immediate_result is not None:
            new_chapter_order_index = current_chapter.order_index + 1
            await self.roadmap_repository.split_chapter_with_new(
                roadmap_id=roadmap.id,
                chapter_id=current_chapter.id,
                mission_ids_to_delete=[m.id for m in pending_missions_sorted],
                new_chapter_title=immediate_result["chapter_title"],
                new_chapter_order_index=new_chapter_order_index,
                new_chapter_missions=immediate_result["missions"],
            )
            changed_count += len(immediate_result["missions"]) + 1  # +1 pelo capítulo em si

            next_starting_order_index = new_chapter_order_index + 1
            unlock_next_leva_immediately = False

        if safe_locked_ids:
            chapters_to_delete = [c for c in locked_chapters if c.id in safe_locked_ids]
            await self.roadmap_repository.replace_locked_chapters(
                roadmap_id=roadmap.id,
                chapter_ids_to_delete=[c.id for c in chapters_to_delete],
                chapters_data=chapters_data,
                starting_order_index=next_starting_order_index,
                ai_generation_log={"chapters": chapters_data},
            )
        else:
            await self.roadmap_repository.append_chapters(
                roadmap_id=roadmap.id,
                chapters_data=chapters_data,
                starting_order_index=next_starting_order_index,
                unlock_first_chapter=unlock_next_leva_immediately,
                ai_generation_log={"chapters": chapters_data},
            )

        changed_count += len(chapters_data)
        return changed_count

    async def _filter_safely_deletable(self, locked_chapters) -> List[int]:
        chapter_ids = [c.id for c in locked_chapters]
        chapters_with_executions = await self.roadmap_repository.get_chapter_ids_with_executions(chapter_ids)
        return [cid for cid in chapter_ids if cid not in chapters_with_executions]

    async def _generate_immediate_chapter(
        self, goal, reflections: List[Dict[str, str]], feedback: Optional[str], pending_count: int
    ) -> Optional[dict]:
        if pending_count == 0:
            return None

        prompt = self._build_common_context(goal, reflections, feedback)
        prompt += f"\n\nQuantidade de missões para o novo capítulo: {pending_count}."

        try:
            result = await self.ai_client.generate_json(
                prompt=prompt,
                system_instruction=IMMEDIATE_SYSTEM_INSTRUCTION,
                response_schema=_build_immediate_schema(pending_count),
            )
        except Exception as exc:  
            raise AdaptationFailedError(f"Não foi possível gerar o ajuste imediato: {exc}") from exc

        if not isinstance(result, dict) or not result.get("chapter_title") or not isinstance(
            result.get("missions"), list
        ):
            raise AdaptationFailedError("Resposta da IA para o ajuste imediato veio em formato inválido.")

        return result

    async def _generate_chapters(
        self, goal, context_chapters, feedback: Optional[str], reflections: List[Dict[str, str]]
    ) -> List[dict]:
        prompt = self._build_common_context(goal, reflections, feedback)
        prompt += "\n\nConteúdo já coberto nesta jornada (NÃO repita nada disso):"
        for chapter in context_chapters:
            mission_titles = ", ".join(m.title for m in chapter.missions)
            prompt += f"\n- Capítulo \"{chapter.title}\" (status: {chapter.status}): {mission_titles}"

        try:
            result = await self.ai_client.generate_json(
                prompt=prompt,
                system_instruction=CHAPTERS_SYSTEM_INSTRUCTION,
            )
        except Exception as exc: 
            raise AdaptationFailedError(f"Não foi possível gerar os próximos capítulos: {exc}") from exc

        if not isinstance(result, dict) or not isinstance(result.get("chapters"), list) or not result["chapters"]:
            raise AdaptationFailedError("Resposta da IA não trouxe 'chapters' válidos.")
        for chapter in result["chapters"]:
            if not isinstance(chapter, dict) or not chapter.get("title") or not chapter.get("missions"):
                raise AdaptationFailedError("Um capítulo da resposta da IA está mal formado.")

        chapters_data = result["chapters"][:6]  # trava de segurança
        for chapter in chapters_data:
            chapter["missions"] = chapter.get("missions", [])[:10]
        return chapters_data

    @staticmethod
    def _build_common_context(goal, reflections: List[Dict[str, str]], feedback: Optional[str]) -> str:
        prompt = f"Objetivo original: {goal.context_prompt}"

        if goal.weekly_active_days is not None:
            prompt += f"\nDias por semana: {goal.weekly_active_days}."
        if goal.daily_time_minutes is not None:
            prompt += f"\nTempo disponível por dia: {goal.daily_time_minutes} minutos."
        if goal.prior_knowledge_level is not None:
            prompt += f"\nConhecimento prévio original: {goal.prior_knowledge_level}."

        if reflections:
            prompt += "\n\nReflexões recentes do usuário sobre as missões concluídas:"
            for item in reflections:
                prompt += f"\n- \"{item['mission_title']}\": {item['reflection']}"

        if feedback:
            prompt += f"\n\nFeedback direto do usuário agora: \"{feedback}\""

        return prompt