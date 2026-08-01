from dataclasses import dataclass
from typing import List

from app.application.goals.moderate_goal_content import ModerateGoalContentUseCase
from app.core.ai.gemini_client import GeminiClient
from app.core.config import settings
from app.domain.repositories.goal_repository import GoalRepository
from app.domain.repositories.user_repository import UserRepository

INTAKE_SYSTEM_INSTRUCTION = """
Você faz DUAS coisas com o pedido de objetivo de um usuário, rápido e sem
neura -- isso roda ANTES da geração de verdade do roadmap.

1. MELHORA A REDAÇÃO: reescreva o pedido do jeito que a pessoa quis dizer,
   só corrigindo clareza/gramática/organização. NUNCA mude o que foi
   pedido, adicione objetivo que a pessoa não mencionou, ou remova algo que
   ela disse. Se o pedido já estiver claro, devolva ele quase igual (pode
   até ser idêntico) -- não reescreva por reescrever.

2. DETECTA INFORMAÇÃO FALTANDO: para alguns tipos de objetivo, existe
   informação prática que muda MUITO o resultado e que a pessoa não deu.
   Exemplos: objetivo de estética/corpo sem peso, altura ou idade;
   objetivo de investir sem saber quanto tem disponível por mês; aprender
   um idioma pra uma viagem sem saber quando é a viagem; objetivo de
   carreira sem saber a área ou nível atual. Se notar algo assim, gere ATÉ
   3 perguntas curtas e diretas (NUNCA mais que 3 -- a pessoa desanima se a
   gente encher de pergunta antes mesmo de começar). Perguntas objetivas,
   com resposta idealmente curta (número, data, escolha entre poucas
   opções) -- nunca perguntas abertas demais.

   Se o pedido já tiver informação suficiente pra montar um roadmap bom,
   NÃO invente pergunta -- devolva a lista vazia. Na dúvida entre perguntar
   ou não, prefira NÃO perguntar: 3 perguntas é o teto de emergência, não a
   meta.

Responda SOMENTE em JSON, neste formato:
{"improved_prompt": "string", "questions": ["string", ...]}
(questions pode ter de 0 a 3 itens; lista vazia é o caso mais comum.)
"""

INTAKE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "improved_prompt": {"type": "STRING"},
        "questions": {
            "type": "ARRAY",
            "maxItems": 3,
            "items": {"type": "STRING"},
        },
    },
    "required": ["improved_prompt", "questions"],
}


@dataclass
class _IntakeAIResult:
    improved_prompt: str
    questions: List[str]


class IntakeGoalUseCase:
    """Roda logo depois da moderação passar: melhora a redação do pedido do
    usuário e detecta se falta alguma informação prática importante pra
    montar um roadmap bom (ex: peso/altura num objetivo de estética). Se
    faltar, gera até 3 perguntas curtas e retorna "awaiting_info" -- quem
    chama (o job handler) NÃO deve prosseguir pra geração nesse caso; espera
    o usuário responder via POST /goals/{id}/answers.

    Devolve uma string com o desfecho: "rejected" | "awaiting_info" |
    "ready" | "not_found". Só no caso "ready" é que faz sentido enfileirar
    a geração de verdade (isso é responsabilidade de quem chama, não deste
    use case -- ver app/core/jobs/handlers.py)."""

    def __init__(
        self,
        goal_repository: GoalRepository,
        user_repository: UserRepository,
        moderation_use_case: ModerateGoalContentUseCase,
        intake_ai_client: GeminiClient,
    ):
        self.goal_repository = goal_repository
        self.user_repository = user_repository
        self.moderation_use_case = moderation_use_case
        self.intake_ai_client = intake_ai_client

    async def execute(self, goal_id: int) -> str:
        goal = await self.goal_repository.get_by_id(goal_id)
        if goal is None:
            return "not_found"

        try:
            moderation = await self.moderation_use_case.execute(goal.context_prompt)
        except Exception as exc:  
            await self.goal_repository.rollback()
            await self.goal_repository.update(
                goal_id, generation_status="failed", generation_error=f"Moderação falhou: {exc}"
            )
            # O roadmap nunca vai ser gerado -- devolve o crédito já cobrado
            # em POST /goals (ver goals.py).
            await self.user_repository.refund_credits(goal.user_id, settings.CREDITS_COST_GENERATE_ROADMAP)
            return "failed"

        if not moderation.is_safe:
            await self.goal_repository.update(
                goal_id,
                title="Objetivo não permitido",
                generation_status="rejected",
                generation_error=moderation.reason,
                category=moderation.category,
                involves_learning=moderation.involves_learning,
            )
            await self.user_repository.refund_credits(goal.user_id, settings.CREDITS_COST_GENERATE_ROADMAP)
            return "rejected"

        await self.goal_repository.update(
            goal_id, category=moderation.category, involves_learning=moderation.involves_learning
        )

        intake_result = await self._run_intake(goal.context_prompt, moderation.category)

        if intake_result.questions:
            await self.goal_repository.update(
                goal_id,
                generation_status="awaiting_info",
                improved_prompt=intake_result.improved_prompt,
                pending_questions=intake_result.questions,
            )
            return "awaiting_info"

        await self.goal_repository.update(goal_id, improved_prompt=intake_result.improved_prompt)
        return "ready"

    async def _run_intake(self, context_prompt: str, category: str) -> _IntakeAIResult:
        prompt = (
            f"Categoria detectada para este objetivo: {category}\n"
            f"Pedido original do usuário: {context_prompt}"
        )
        try:
            result = await self.intake_ai_client.generate_json(
                prompt=prompt,
                system_instruction=INTAKE_SYSTEM_INSTRUCTION,
                response_schema=INTAKE_SCHEMA,
            )
        except Exception:
            # A triagem é um bônus -- se ela falhar (rede, formato, etc.),
            # a geração do roadmap não pode ficar travada por causa disso.
            # Segue com o prompt original e sem perguntas.
            return _IntakeAIResult(improved_prompt=context_prompt, questions=[])

        improved_prompt = str(result.get("improved_prompt") or "").strip() or context_prompt
        raw_questions = result.get("questions")
        questions = (
            [str(q).strip() for q in raw_questions if str(q).strip()][:3]
            if isinstance(raw_questions, list)
            else []
        )
        return _IntakeAIResult(improved_prompt=improved_prompt, questions=questions)
