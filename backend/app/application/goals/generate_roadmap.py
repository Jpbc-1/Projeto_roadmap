from datetime import date

from app.application.goals.moderate_goal_content import ModerateGoalContentUseCase
from app.core.ai.gemini_client import GeminiClient
from app.domain.repositories.goal_repository import GoalRepository
from app.domain.repositories.roadmap_repository import RoadmapRepository

ROADMAP_SYSTEM_INSTRUCTION = """
Você é a IA do Roadmap AI, um aplicativo que transforma objetivos grandes em
planos de aprendizado divididos em capítulos e missões diárias pequenas e
executáveis, no estilo "Duolingo para a vida".

O roadmap NÃO precisa cobrir o objetivo inteiro de uma vez — ele é adaptativo
e será estendido automaticamente conforme o usuário avança. Sua tarefa é
gerar apenas a PRIMEIRA LEVA de capítulos: o suficiente para o usuário
começar a progredir de verdade agora, terminando num ponto de checkpoint
natural (ex: domina os fundamentos, completa a primeira fase, chega a um
marco intermediário claro) — não o plano completo até a data-alvo.

Use a descrição do objetivo (e a data-alvo, se houver) só para calibrar o
RITMO e a PROFUNDIDADE dos capítulos que você gerar agora, não para tentar
prever todos os capítulos futuros:
- Objetivos de curto prazo (semanas): a primeira leva provavelmente já cobre
  o objetivo inteiro.
- Objetivos de longo prazo (meses): gere só as primeiras semanas de jornada,
  terminando num checkpoint natural — o resto será gerado depois.

Se o usuário informou quantos dias por semana pretende se dedicar e/ou
quanto tempo por dia tem disponível, use isso para calibrar o ritmo real:
- Poucos dias por semana (ex: 2-3) ou pouco tempo por dia: gere menos
  missões por capítulo (dentro do limite abaixo) e prefira missões mais
  curtas — não tente compensar espremendo conteúdo demais nos dias
  disponíveis.
- Se o usuário não informar nada, decida você mesmo um ritmo saudável e
  sustentável, incluindo variação de intensidade entre missões (nem toda
  missão precisa ser igualmente pesada) — construa a sensação de dias mais
  leves dentro da própria sequência de missões.

Se o usuário informou seu nível de conhecimento prévio (iniciante,
intermediário ou avançado), calibre a profundidade e o ponto de partida:
não repita fundamentos que a pessoa já domina.

Dentro dessa primeira leva, gere quantos capítulos fizerem sentido para
alcançar esse checkpoint de forma coerente (normalmente entre 2 e 10, mas
use julgamento, não uma contagem fixa).

Cada capítulo deve ter entre 3 e 7 missões diárias pequenas, específicas e
realizáveis dentro do tempo disponível por dia informado (ou até 60 minutos,
se não informado) — esse limite de missões por capítulo é proposital, para
manter o ritmo de progresso diário motivador.

Também gere:
- Um título curto e motivador para o objetivo como um todo (máximo 60
  caracteres);
- Uma estimativa de quantas semanas o objetivo completo (não só essa
  primeira leva) deve levar para ser alcançado, no ritmo informado ou no
  ritmo que você mesmo calibrou (campo "estimated_completion_weeks", um
  número inteiro).

Responda SOMENTE em JSON válido, sem nenhum texto antes ou depois, exatamente
neste formato (isto é um EXEMPLO ilustrativo de estrutura, não copie o
conteúdo, gere o conteúdo real baseado no objetivo do usuário):

{
  "title": "Aprenda Python do Zero",
  "estimated_completion_weeks": 6,
  "chapters": [
    {
      "title": "Fundamentos da Linguagem",
      "missions": [
        {"title": "Instale o Python", "description": "Configure seu ambiente de desenvolvimento", "estimated_minutes": 20},
        {"title": "Variáveis e tipos", "description": "Aprenda os tipos básicos de dados", "estimated_minutes": 30}
      ]
    }
  ]
}
"""


class RoadmapFormatError(Exception):
    """Levantado quando o JSON devolvido pela IA não tem o formato esperado."""


class GenerateRoadmapUseCase:
    """Orquestra: moderação -> geração -> persistência.

    Contrato importante: este caso de uso NUNCA deixa uma exceção escapar.
    Ele sempre termina atualizando o goal para um estado definitivo
    (completed | rejected | failed), porque quem o chama é uma tarefa em
    background — se uma exceção escapasse aqui, ninguém estaria "ouvindo"
    pra tratar o erro, e o goal ficaria preso em "pending" para sempre.
    """

    def __init__(
        self,
        goal_repository: GoalRepository,
        roadmap_repository: RoadmapRepository,
        moderation_use_case: ModerateGoalContentUseCase,
        ai_client: GeminiClient,
    ):
        self.goal_repository = goal_repository
        self.roadmap_repository = roadmap_repository
        self.moderation_use_case = moderation_use_case
        self.ai_client = ai_client

    async def execute(self, goal_id: int) -> None:
        goal = await self.goal_repository.get_by_id(goal_id)
        if goal is None:
            return

        try:
            moderation = await self.moderation_use_case.execute(goal.context_prompt)

            if not moderation.is_safe:
                await self.goal_repository.update(
                    goal_id,
                    title="Objetivo não permitido",
                    generation_status="rejected",
                    generation_error=moderation.reason,
                )
                return

            result = await self.ai_client.generate_json(
                prompt=self._build_generation_prompt(goal),
                system_instruction=ROADMAP_SYSTEM_INSTRUCTION,
            
            )
            self._validate_format(result)
            self._apply_safety_limits(result)

            await self.roadmap_repository.create_full_roadmap(
                goal_id=goal.id,
                version=1,
                ai_generation_log=result,
                chapters_data=result["chapters"],
            )

            await self.goal_repository.update(
                goal_id,
                title=result["title"],
                generation_status="completed",
                estimated_completion_weeks=self._extract_estimated_weeks(result),
            )

        except Exception as exc:  
            await self.goal_repository.update(
                goal_id,
                generation_status="failed",
                generation_error=str(exc),
            )

    @staticmethod
    def _build_generation_prompt(goal) -> str:
        prompt = f"Objetivo do usuário: {goal.context_prompt}"

        if goal.target_date is not None:
            prompt += (
                f"\nData-alvo desejada pelo usuário: {goal.target_date.isoformat()} "
                f"(hoje é {date.today().isoformat()}). Use isso só para calibrar o "
                "ritmo da primeira leva de capítulos, não para tentar planejar até lá."
            )

        if goal.weekly_active_days is not None:
            prompt += f"\nDias por semana que o usuário pretende se dedicar: {goal.weekly_active_days}."

        if goal.daily_time_minutes is not None:
            prompt += f"\nTempo disponível por dia: aproximadamente {goal.daily_time_minutes} minutos."

        if goal.prior_knowledge_level is not None:
            level_labels = {
                "beginner": "iniciante, sem conhecimento prévio no assunto",
                "intermediate": "conhecimento intermediário no assunto",
                "advanced": "conhecimento avançado no assunto",
            }
            prompt += f"\nNível de conhecimento prévio do usuário: {level_labels[goal.prior_knowledge_level]}."

        return prompt

    @staticmethod
    def _extract_estimated_weeks(result: dict) -> "int | None":
        """Campo 'bônus', não crítico -- se a IA não trouxer ou trouxer algo
        que não é um número válido, seguimos sem quebrar a geração por causa
        disso (diferente de 'title'/'chapters', que são essenciais)."""
        value = result.get("estimated_completion_weeks")
        if isinstance(value, bool):  # bool é subclasse de int em Python -- descarta explicitamente
            return None
        if isinstance(value, int) and value > 0:
            return value
        return None

    @staticmethod
    def _validate_format(result: dict) -> None:
        """Sem response_schema, a IA pode (raramente) fugir do formato
        pedido -- validamos aqui em vez de deixar um KeyError genérico
        estourar lá na frente, para uma mensagem de erro clara em
        generation_error."""
        if not isinstance(result, dict):
            raise RoadmapFormatError("Resposta da IA não é um objeto JSON.")

        if not isinstance(result.get("title"), str) or not result["title"].strip():
            raise RoadmapFormatError("Resposta da IA não trouxe um 'title' válido.")

        chapters = result.get("chapters")
        if not isinstance(chapters, list) or len(chapters) == 0:
            raise RoadmapFormatError("Resposta da IA não trouxe 'chapters' válidos.")

        for chapter in chapters:
            if not isinstance(chapter, dict) or not chapter.get("title"):
                raise RoadmapFormatError("Um capítulo da resposta da IA está mal formado.")
            missions = chapter.get("missions")
            if not isinstance(missions, list) or len(missions) == 0:
                raise RoadmapFormatError(f"Capítulo '{chapter.get('title')}' sem missões válidas.")
            for mission in missions:
                if not isinstance(mission, dict) or not mission.get("title"):
                    raise RoadmapFormatError(f"Uma missão do capítulo '{chapter.get('title')}' está mal formada.")

    @staticmethod
    def _apply_safety_limits(result: dict) -> None:
        """Trava de segurança técnica (não de produto): se por qualquer
        motivo a IA devolver algo fora do razoável, cortamos aqui em Python
        -- em vez de tentar forçar isso no schema do Gemini, que causa erro
        de "too many states for serving" quando arrays aninhados têm limite
        de tamanho nos dois níveis ao mesmo tempo."""
        MAX_CHAPTERS = 20
        MAX_MISSIONS_PER_CHAPTER = 10

        chapters = result.get("chapters", [])[:MAX_CHAPTERS]
        for chapter in chapters:
            chapter["missions"] = chapter.get("missions", [])[:MAX_MISSIONS_PER_CHAPTER]
        result["chapters"] = chapters