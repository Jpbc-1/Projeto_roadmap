from dataclasses import dataclass
from typing import List, Optional

from app.application.goals.moderate_goal_content import ModerateGoalContentUseCase
from app.core.ai.gemini_client import GeminiClient
from app.core.ai.prompt_safety import PROMPT_INJECTION_GUARD, wrap_user_text
from app.core.config import settings
from app.core.error_sanitization import safe_error_message
from app.domain.repositories.goal_repository import GoalRepository
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.database.models import Goal

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

   IMPORTANTE -- o prompt que você recebe pode trazer uma seção
   "Informações que a pessoa já forneceu": é dado de formulário
   estruturado, preenchido ANTES desta triagem rodar. NUNCA gere pergunta
   sobre nada que já apareça ali, mesmo com redação ou unidade diferente.
   Exemplo real que JÁ aconteceu e não pode se repetir: a pessoa informou
   "90 minutos por dia" no formulário, e a triagem perguntou "quantas horas
   por semana você tem disponível" -- isso é o mesmo dado, só que a pessoa
   já tinha dado. Se precisar converter unidade (minutos/dia x dias/semana
   = minutos/semana), faça a conta você mesmo; nunca devolva esse trabalho
   pra pessoa em forma de pergunta.

Responda SOMENTE em JSON, neste formato:
{"improved_prompt": "string", "questions": ["string", ...]}
(questions pode ter de 0 a 3 itens; lista vazia é o caso mais comum.)
""" + PROMPT_INJECTION_GUARD

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
                goal_id,
                generation_status="failed",
                generation_error=safe_error_message(exc, "Não foi possível moderar seu objetivo"),
            )
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
            return "rejected"

        await self.goal_repository.update(
            goal_id, category=moderation.category, involves_learning=moderation.involves_learning
        )

        intake_result = await self._run_intake(goal, moderation.category)

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

    async def _run_intake(self, goal: Goal, category: str) -> _IntakeAIResult:
        prompt = (
            f"Categoria detectada para este objetivo: {category}\n"
            f"Pedido original do usuário:\n{wrap_user_text(goal.context_prompt)}"
            f"{self._format_known_facts(goal)}"
        )
        try:
            result = await self.intake_ai_client.generate_json(
                prompt=prompt,
                system_instruction=INTAKE_SYSTEM_INSTRUCTION,
                response_schema=INTAKE_SCHEMA,
            )
        except Exception:
            return _IntakeAIResult(improved_prompt=goal.context_prompt, questions=[])

        improved_prompt = str(result.get("improved_prompt") or "").strip() or goal.context_prompt
        raw_questions = result.get("questions")
        questions = (
            [str(q).strip() for q in raw_questions if str(q).strip()][:3]
            if isinstance(raw_questions, list)
            else []
        )
        return _IntakeAIResult(improved_prompt=improved_prompt, questions=questions)

    @staticmethod
    def _format_known_facts(goal: Goal) -> str:
        """Monta a seção de 'já respondido' a partir dos campos estruturados
        que a pessoa preenche em POST /goals (ver GoalCreate) -- é o que
        faltava antes: esses campos existiam no banco, mas nunca chegavam
        no prompt da triagem, então a IA não tinha como saber que já
        estavam preenchidos e podia (e às vezes fazia) perguntar nesses
        mesmos assuntos de novo."""
        facts = []
        if goal.daily_time_minutes:
            facts.append(f"- Tempo disponível por dia: {goal.daily_time_minutes} minutos")
        if goal.weekly_active_days:
            facts.append(f"- Dias ativos por semana: {goal.weekly_active_days}")
        if goal.prior_knowledge_level:
            facts.append(f"- Nível de conhecimento prévio: {goal.prior_knowledge_level}")
        if goal.target_date:
            facts.append(f"- Data alvo: {goal.target_date.isoformat()}")

        if not facts:
            return ""

        return (
            "\nInformações que a pessoa já forneceu (campos de formulário, "
            "preenchidos antes desta triagem -- não pergunte de novo sobre "
            "nada disto):\n" + "\n".join(facts)
        )
