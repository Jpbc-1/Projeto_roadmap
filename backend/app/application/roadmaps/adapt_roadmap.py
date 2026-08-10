import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.application.goals.generate_roadmap import CATEGORY_GUIDANCE
from app.application.goals.get_goal import GoalAccessDeniedError, GoalNotFoundError
from app.core.ai.gemini_client import GeminiClient
from app.core.ai.prompt_safety import PROMPT_INJECTION_GUARD, wrap_user_text
from app.domain.repositories.goal_repository import GoalRepository
from app.domain.repositories.recommendation_repository import RecommendationRepository
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
houver sinal para isso). Mantenha o título curto (até 40 caracteres) --
precisa caber bem em telas pequenas do app. Gere EXATAMENTE a quantidade de
missões pedida.

Ajuste dificuldade e ritmo conforme os sinais recebidos: se indicarem que
está fácil/lento, torne mais denso e avance mais rápido; se indicarem
dificuldade ou cansaço, torne mais leve e inclua ao menos uma missão de
"descanso ativo" (revisão leve, sem conteúdo novo). Sem nenhum sinal,
mantenha o ritmo coerente com o que já vinha sendo usado.

Para CADA missão, classifique também se ela é CONCEITUAL (conhecimento,
terminologia ou técnica que vale revisar depois) ou uma AÇÃO PRÁTICA/de
configuração (feita uma vez, não precisa ser "relembrada" -- ex: "instale
uma ferramenta", "monte seu currículo"). Marque isso no campo booleano
"is_conceptual" de cada missão.
""" + PROMPT_INJECTION_GUARD


def _build_immediate_schema(missions_count: int, include_goal_title: bool = False) -> Dict[str, Any]:
    """Schema com minItems=maxItems=missions_count -- força a IA a devolver
    a quantidade EXATA de missões pedida. Seguro de usar aqui porque é um
    array de 1 nível só (sem array aninhado dentro de array, que foi o que
    causou o erro 'too many states for serving' na geração de capítulos).

    include_goal_title: quando True (capítulo 1 sendo substituído), também
    exige um novo título pro objetivo E novas recomendações -- ver
    comentário em _generate_immediate_chapter."""
    properties: Dict[str, Any] = {
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
                    "is_conceptual": {"type": "BOOLEAN"},
                },
                "required": ["title", "description", "estimated_minutes", "is_conceptual"],
            },
        },
    }
    required = ["chapter_title", "missions"]

    if include_goal_title:
        properties["new_goal_title"] = {"type": "STRING"}
        required.append("new_goal_title")
        properties["recommendations"] = {
            "type": "ARRAY",
            "maxItems": 6,
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING"},
                    "description": {"type": "STRING"},
                    "is_paid": {"type": "BOOLEAN"},
                },
                "required": ["name", "description", "is_paid"],
            },
        }
        required.append("recommendations")

    return {"type": "OBJECT", "properties": properties, "required": required}


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
- Títulos de capítulo curtos (até 40 caracteres), mas específicos o
  bastante para entender do que se trata.
- Para CADA missão, classifique se ela é CONCEITUAL (conhecimento/técnica
  que vale revisar depois) ou uma AÇÃO PRÁTICA (feita uma vez, não precisa
  ser "relembrada"), no campo booleano "is_conceptual".

Responda SOMENTE em JSON válido, sem texto antes ou depois, neste formato:

{
  "chapters": [
    {
      "title": "string",
      "missions": [
        {"title": "string", "description": "string", "estimated_minutes": number, "is_conceptual": true ou false}
      ]
    }
  ]
}
""" + PROMPT_INJECTION_GUARD


class AdaptationFailedError(Exception):
    """Levantado quando a IA falha ou devolve algo em formato inválido.

    status_code carrega o HTTP status da falha de origem quando ela veio
    de uma GeminiAPIError (ex: 503 = sobrecarregado mesmo depois de
    esgotar toda a cadeia de fallback) -- None quando a causa não tem um
    status HTTP claro (ex: resposta em formato inesperado). O endpoint usa
    isso pra devolver 503 (tente de novo already) em vez de um 502 genérico
    quando faz sentido."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class AdaptationResult:
    """Antes disso, execute() devolvia um único int somando missão do
    capítulo imediato + 1 (o capítulo em si) + capítulos futuros -- um
    número sem unidade coerente, chamado de "new_chapters_count" no
    endpoint mesmo não sendo uma contagem de capítulos de verdade.
    Separado em dois campos com nome e unidade claros."""

    chapters_changed: int
    missions_changed: int


class AdaptRoadmapUseCase:
    def __init__(
        self,
        goal_repository: GoalRepository,
        roadmap_repository: RoadmapRepository,
        recommendation_repository: RecommendationRepository,
        ai_client: GeminiClient,
    ):
        self.goal_repository = goal_repository
        self.roadmap_repository = roadmap_repository
        self.recommendation_repository = recommendation_repository
        self.ai_client = ai_client

    async def execute(self, goal_id: int, user_id: int, feedback: Optional[str]) -> AdaptationResult:
        """Aplica o feedback amplo (ver módulo propose_chapter_operation.py
        pro caminho de capítulo específico) -- substitui o restante do
        capítulo atual e/ou os capítulos futuros. Devolve quantos capítulos
        e quantas missões foram alterados, como dois números separados."""
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
        is_first_chapter = current_chapter is not None and current_chapter.order_index == 0

        pending_missions_sorted = []
        reflections: List[Dict[str, Any]] = []
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
            goal, reflections, feedback, len(pending_missions_sorted), is_first_chapter
        )
        chapters_task = self._generate_chapters(goal, context_chapters, feedback, reflections)
        immediate_result, chapters_data = await asyncio.gather(immediate_task, chapters_task)

        changed_chapters = 0
        changed_missions = 0
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
            changed_chapters += 1
            changed_missions += len(immediate_result["missions"])

            next_starting_order_index = new_chapter_order_index + 1
            unlock_next_leva_immediately = False

            if is_first_chapter:
                new_title = str(immediate_result.get("new_goal_title", "")).strip()[:40]
                if new_title:
                    await self.goal_repository.update(goal.id, title=new_title)

                new_recommendations = immediate_result.get("recommendations")
                if isinstance(new_recommendations, list) and new_recommendations:
                    await self.recommendation_repository.delete_by_goal(goal.id)
                    await self.recommendation_repository.bulk_create(goal.id, new_recommendations[:6])

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

        changed_chapters += len(chapters_data)
        changed_missions += sum(len(c.get("missions", [])) for c in chapters_data)
        return AdaptationResult(chapters_changed=changed_chapters, missions_changed=changed_missions)

    async def _filter_safely_deletable(self, locked_chapters) -> List[int]:
        """Um capítulo só entra na leva que pode ser substituída pela
        adaptação ampla se: (1) ninguém começou nenhuma missão dele ainda
        (senão apagaria progresso real), e (2) não está travado contra a IA
        (is_locked_from_ai) -- a mesma trava que o fluxo de operação
        específica já respeitava, agora vale pro fluxo amplo também."""
        chapter_ids = [c.id for c in locked_chapters if not c.is_locked_from_ai]
        if not chapter_ids:
            return []
        chapters_with_executions = await self.roadmap_repository.get_chapter_ids_with_executions(chapter_ids)
        return [cid for cid in chapter_ids if cid not in chapters_with_executions]

    async def _generate_immediate_chapter(
        self,
        goal,
        reflections: List[Dict[str, Any]],
        feedback: Optional[str],
        pending_count: int,
        is_first_chapter: bool,
    ) -> Optional[dict]:
        if pending_count == 0:
            return None

        prompt = self._build_common_context(goal, reflections, feedback)
        prompt += f"\n\nQuantidade de missões para o novo capítulo: {pending_count}."

        if is_first_chapter:
            prompt += (
                "\n\nEste capítulo está substituindo o CAPÍTULO 1 do roadmap -- "
                "a pessoa está adaptando antes mesmo de terminar o começo da "
                "jornada. Por isso: (1) a PRIMEIRA missão deste novo capítulo "
                "também deve ser uma \"vitória rápida\": propositalmente curta "
                "e fácil (5 a 10 minutos), pra dar o mesmo gás inicial que o "
                "capítulo 1 original daria; (2) como o rumo do objetivo está "
                "mudando logo no início, gere também um novo título curto para "
                "o OBJETIVO como um todo (campo \"new_goal_title\", até 40 "
                "caracteres) -- o título antigo foi baseado no pedido original "
                "e pode não fazer mais sentido; (3) gere também novas "
                "\"recommendations\" (0 a 3 pagas + 0 a 3 gratuitas, mesmos "
                "critérios de sempre -- sem inventar, sem URL) para o rumo "
                "NOVO -- as antigas eram do rumo anterior e vão ser trocadas "
                "por essas."
            )

        try:
            result = await self.ai_client.generate_json(
                prompt=prompt,
                system_instruction=IMMEDIATE_SYSTEM_INSTRUCTION,
                response_schema=_build_immediate_schema(pending_count, include_goal_title=is_first_chapter),
            )
        except Exception as exc:  
            raise AdaptationFailedError(
                f"Não foi possível gerar o ajuste imediato: {exc}",
                status_code=getattr(exc, "status_code", None),
            ) from exc

        if not isinstance(result, dict) or not result.get("chapter_title") or not isinstance(
            result.get("missions"), list
        ):
            raise AdaptationFailedError("Resposta da IA para o ajuste imediato veio em formato inválido.")

        return result

    async def _generate_chapters(
        self, goal, context_chapters, feedback: Optional[str], reflections: List[Dict[str, Any]]
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
            raise AdaptationFailedError(
                f"Não foi possível gerar os próximos capítulos: {exc}",
                status_code=getattr(exc, "status_code", None),
            ) from exc

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
    def _build_common_context(goal, reflections: List[Dict[str, Any]], feedback: Optional[str]) -> str:
        prompt = f"Objetivo original:\n{wrap_user_text(goal.context_prompt)}"

        if goal.weekly_active_days is not None:
            prompt += f"\nDias por semana: {goal.weekly_active_days}."
        if goal.daily_time_minutes is not None:
            prompt += f"\nTempo disponível por dia: {goal.daily_time_minutes} minutos."
        if goal.prior_knowledge_level is not None:
            prompt += f"\nConhecimento prévio original: {goal.prior_knowledge_level}."

        category_guidance = CATEGORY_GUIDANCE.get(goal.category)
        if category_guidance:
            prompt += f"\n{category_guidance}"

        if reflections:
            prompt += "\n\nReflexões e sinais recentes do usuário sobre as missões concluídas:"
            for item in reflections:
                line = f"\n- \"{item['mission_title']}\""
                details = []
                if item.get("reflection"):
                    details.append(f"reflexão: {wrap_user_text(item['reflection'], 'reflexao')}")
                if item.get("difficulty_rating"):
                    details.append(f"dificuldade sentida: {item['difficulty_rating']}")
                if item.get("satisfaction_rating") is not None:
                    details.append(f"satisfação com o roadmap: {item['satisfaction_rating']}/5")
                if details:
                    line += " (" + "; ".join(details) + ")"
                prompt += line

        if feedback:
            prompt += f"\n\nFeedback direto do usuário agora:\n{wrap_user_text(feedback, 'feedback_do_usuario')}"

        return prompt