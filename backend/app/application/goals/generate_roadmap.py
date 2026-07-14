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

Dentro dessa primeira leva, gere quantos capítulos fizerem sentido para
alcançar esse checkpoint de forma coerente (normalmente entre 2 e 10, mas
use julgamento, não uma contagem fixa).

Cada capítulo deve ter entre 3 e 7 missões diárias pequenas, específicas e
realizáveis em até 60 minutos cada — esse limite de missões por capítulo é
proposital, para manter o ritmo de progresso diário motivador.

Também gere um título curto e motivador para o objetivo como um todo
(máximo 60 caracteres).

Responda SOMENTE em JSON válido, sem nenhum texto antes ou depois, exatamente
neste formato (isto é um EXEMPLO ilustrativo de estrutura, não copie o
conteúdo, gere o conteúdo real baseado no objetivo do usuário):

{
  "title": "Aprenda Python do Zero",
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
            # Não deveria acontecer (o goal acabou de ser criado), mas se
            # acontecer não há goal pra atualizar -> só encerra.
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
                # Sem response_schema aqui de propósito: um schema com objetos
                # aninhados dentro de arrays (capítulo -> missões) ultrapassa
                # o limite de complexidade do validador estruturado do
                # Gemini ("too many states for serving"). O formato mesmo
                # assim vem confiável porque o prompt já descreve a estrutura
                # exata com um exemplo, e validamos abaixo em Python.
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
            )

        except Exception as exc:  # noqa: BLE001 - intencional: é a "rede de segurança" final
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
        return prompt

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