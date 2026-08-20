import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.application.goals.get_goal import GoalAccessDeniedError, GoalNotFoundError
from app.application.roadmaps.get_roadmap import RoadmapNotFoundError
from app.core.ai.gemini_client import GeminiClient
from app.core.ai.prompt_safety import PROMPT_INJECTION_GUARD, wrap_user_text
from app.domain.repositories.goal_repository import GoalRepository
from app.domain.repositories.roadmap_repository import RoadmapRepository

CHAPTER_OPERATION_SYSTEM_INSTRUCTION = """
Você decide como um pedido de ajuste (feedback) de um roadmap deve ser
tratado -- classificando o "scope" e, quando fizer sentido, propondo uma
operação específica em vez de deixar o sistema regenerar tudo à frente.

Primeiro, classifique o "scope" do feedback:
- "chapter_operation": o feedback aponta claramente pra UM capítulo
  específico já existente na lista (a pessoa menciona o número/nome/
  conteúdo de um capítulo certo), OU pede claramente pra ADICIONAR um
  capítulo novo em algum ponto específico do roadmap (ex: "depois do
  capítulo 3").
- "broad": o feedback é sobre ritmo, dificuldade geral, motivação, ou
  direção do roadmap como um todo -- não aponta pra nenhum capítulo
  específico. Também use "broad" se o feedback for ambíguo demais pra
  saber com confiança qual capítulo é.

Se "scope" for "chapter_operation", preencha "operation" com UMA das duas:
- type "replace_chapter": reescreve o conteúdo de um capítulo EXISTENTE
  ("target_chapter_id" = id desse capítulo, olhando a lista fornecida). Use
  quando o pedido é pra MUDAR o que já está lá.
- type "insert_chapter": cria um capítulo NOVO logo depois de um capítulo
  existente ("target_chapter_id" = id do capítulo depois do qual inserir).
  Use quando o pedido é pra ADICIONAR algo, não substituir.

Regras importantes, sem exceção:
- NUNCA proponha uma operação mirando um capítulo com status "completed"
  (já concluído -- não dá pra editar o passado) nem um capítulo com
  "locked_from_ai": true (o usuário bloqueou esse capítulo de propósito).
  Se o pedido do usuário for sobre um capítulo assim, devolva "scope":
  "broad" e não inclua "operation" -- mesmo que dê pra entender o pedido.
- "summary": uma frase curta (até 100 caracteres) descrevendo a mudança
  proposta, que será mostrada ao usuário para ele confirmar ANTES de
  qualquer coisa ser aplicada de verdade (ex: "Reescrever o Capítulo 2 com
  foco em X" ou "Adicionar capítulo sobre Y depois do Capítulo 3").
- O capítulo novo/reescrito segue os MESMOS critérios de sempre: título
  curto (até 40 caracteres), de 3 a 7 missões, cada uma classificada como
  conceitual ou prática no campo "is_conceptual".
- Se "scope" for "broad", NÃO preencha "operation" (omita ou deixe null).

Responda SOMENTE em JSON no formato do schema fornecido.
""" + PROMPT_INJECTION_GUARD

CHAPTER_OPERATION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "scope": {"type": "STRING", "enum": ["chapter_operation", "broad"]},
        "operation": {
            "type": "OBJECT",
            "properties": {
                "type": {"type": "STRING", "enum": ["replace_chapter", "insert_chapter"]},
                "target_chapter_id": {"type": "INTEGER"},
                "summary": {"type": "STRING"},
                "new_chapter": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING"},
                        "missions": {
                            "type": "ARRAY",
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
                    },
                    "required": ["title", "missions"],
                },
            },
            "required": ["type", "target_chapter_id", "summary", "new_chapter"],
        },
    },
    "required": ["scope"],
}


class NoActionableFeedbackError(Exception):
    """Levantado quando não há feedback nem sinais suficientes para propor
    qualquer coisa (ex: chamado sem feedback e sem reflexões novas)."""


@dataclass
class ChapterOperationResult:
    scope: str  
    operation: Optional[Dict[str, Any]] = None
    roadmap_id: Optional[int] = None


class ProposeChapterOperationUseCase:
    """Primeira parada de qualquer pedido de adaptação: decide se o
    feedback mira um capítulo específico. Se sim, GERA a operação mas NÃO
    aplica -- só guarda como proposta pendente no roadmap
    (roadmap.pending_adaptation), pra o usuário confirmar depois via
    ConfirmAdaptationUseCase. Se o scope for "broad" (ou a IA tentou mirar
    um capítulo protegido/concluído), devolve scope="broad" e quem chamou
    deve cair pro fluxo de sempre (AdaptRoadmapUseCase, que continua
    aplicando direto, sem confirmação -- esse comportamento não mudou)."""

    def __init__(
        self,
        goal_repository: GoalRepository,
        roadmap_repository: RoadmapRepository,
        ai_client: GeminiClient,
    ):
        self.goal_repository = goal_repository
        self.roadmap_repository = roadmap_repository
        self.ai_client = ai_client

    async def execute(self, goal_id: int, user_id: int, feedback: Optional[str]) -> ChapterOperationResult:
        goal = await self.goal_repository.get_by_id(goal_id)
        if goal is None:
            raise GoalNotFoundError(f"Objetivo {goal_id} não encontrado.")
        if goal.user_id != user_id:
            raise GoalAccessDeniedError("Você não tem acesso a este objetivo.")

        roadmap = await self.roadmap_repository.get_active_by_goal(goal_id)
        if roadmap is None or not roadmap.chapters:
            raise RoadmapNotFoundError("Nenhum roadmap ativo para este objetivo ainda.")

        if not feedback or not feedback.strip():
            return ChapterOperationResult(scope="broad", roadmap_id=roadmap.id)

        chapters_context = [
            {
                "id": chapter.id,
                "title": chapter.title,
                "status": chapter.status,
                "locked_from_ai": chapter.is_locked_from_ai,
            }
            for chapter in roadmap.chapters
        ]
        prompt = (
            f"Feedback do usuário: {wrap_user_text(feedback.strip())}\n\n"
            f"Capítulos existentes neste roadmap:\n{json.dumps(chapters_context, ensure_ascii=False, indent=2)}"
        )

        try:
            result = await self.ai_client.generate_json(
                prompt=prompt,
                system_instruction=CHAPTER_OPERATION_SYSTEM_INSTRUCTION,
                response_schema=CHAPTER_OPERATION_SCHEMA,
            )
        except Exception:
            return ChapterOperationResult(scope="broad", roadmap_id=roadmap.id)

        scope = result.get("scope") if isinstance(result, dict) else None
        operation = result.get("operation") if isinstance(result, dict) else None

        if scope != "chapter_operation" or not isinstance(operation, dict):
            return ChapterOperationResult(scope="broad", roadmap_id=roadmap.id)

        target_chapter = next(
            (c for c in roadmap.chapters if c.id == operation.get("target_chapter_id")), None
        )
        operation_type = operation.get("type")
        new_chapter = operation.get("new_chapter")

        if (
            target_chapter is None
            or target_chapter.status == "completed"
            or target_chapter.is_locked_from_ai
            or operation_type not in ("replace_chapter", "insert_chapter")
            or not isinstance(new_chapter, dict)
            or not new_chapter.get("title")
            or not isinstance(new_chapter.get("missions"), list)
            or not new_chapter["missions"]
        ):
            return ChapterOperationResult(scope="broad", roadmap_id=roadmap.id)

        await self.roadmap_repository.set_pending_adaptation(roadmap.id, operation)

        return ChapterOperationResult(scope="chapter_operation", operation=operation, roadmap_id=roadmap.id)
