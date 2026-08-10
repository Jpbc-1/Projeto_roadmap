from datetime import date

from app.core.ai.gemini_client import GeminiClient
from app.core.ai.prompt_safety import PROMPT_INJECTION_GUARD, wrap_user_text
from app.core.config import settings
from app.core.error_sanitization import safe_error_message
from app.domain.repositories.goal_repository import GoalRepository
from app.domain.repositories.recommendation_repository import RecommendationRepository
from app.domain.repositories.roadmap_repository import RoadmapRepository
from app.domain.repositories.user_repository import UserRepository

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

Para CADA missão, classifique também se ela é CONCEITUAL (envolve aprender e
reter um conceito, fato, terminologia ou técnica — algo que faz sentido
revisar depois) ou uma AÇÃO PRÁTICA/de configuração (uma tarefa que, uma vez
feita, não precisa ser "relembrada" — ex: "instale o Python", "configure seu
ambiente", "abra uma conta em uma corretora", "monte seu currículo"). Marque
isso no campo booleano "is_conceptual" de cada missão — isso decide se ela
entra no sistema de revisão espaçada depois, então não marque true por
padrão sem pensar: a maioria das missões do primeiro capítulo de setup
costuma ser false.

Também gere:
- Um título curto e motivador para o objetivo como um todo (máximo 40
  caracteres — precisa caber bem em telas pequenas do app, então prefira
  algo direto: "Aprenda Python", não "Um Guia Completo Para Aprender Python
  do Absoluto Zero");
- Títulos de capítulo também curtos (máximo 40 caracteres), mas ainda
  específicos o bastante para a pessoa entender do que se trata sem abrir o
  capítulo;
- Uma estimativa de quantas semanas o objetivo completo (não só essa
  primeira leva) deve levar para ser alcançado, no ritmo informado ou no
  ritmo que você mesmo calibrou (campo "estimated_completion_weeks", um
  número inteiro).

IMPORTANTE sobre a primeiríssima missão do roadmap (a missão 1 do capítulo
1): ela deve ser propositalmente curta e fácil — bem mais rápida que a
média das outras (ex: 5 a 10 minutos), mesmo que isso quebre um pouco a
progressão natural de dificuldade. É a primeira coisa que a pessoa vai
fazer no app, então o objetivo dela é dar uma vitória rápida e gerar
motivação para continuar, não testar a pessoa.

Por fim, sugira de 0 a 3 recursos PAGOS e de 0 a 3 recursos GRATUITOS
(apps, cursos, livros, comunidades, ferramentas, canais) que ajudariam
especificamente NESSE objetivo -- só inclua algo que você tenha confiança
real que existe de verdade e é relevante; é preferível devolver menos itens
(ou nenhum) do que preencher a lista com algo genérico ou inventado. NÃO
inclua links/URLs -- eles não são confiáveis vindos de você; só o nome do
recurso e uma frase curta de por que ajuda, campo "recommendations".

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
        {"title": "Instale o Python", "description": "Configure seu ambiente de desenvolvimento", "estimated_minutes": 20, "is_conceptual": false},
        {"title": "Variáveis e tipos", "description": "Aprenda os tipos básicos de dados", "estimated_minutes": 30, "is_conceptual": true}
      ]
    }
  ],
  "recommendations": [
    {"name": "Codecademy Python", "description": "Curso interativo com exercícios no navegador", "is_paid": true},
    {"name": "python.org/docs", "description": "Documentação oficial, referência gratuita e completa", "is_paid": false}
  ]
}
""" + PROMPT_INJECTION_GUARD


CATEGORY_GUIDANCE = {
    "FITNESS": """
Este objetivo é de FITNESS. A pessoa quer resultado físico e organização de
rotina, não uma aula de biologia. NÃO crie missões de teoria/anatomia que
não mudam a ação prática do dia a dia (ex: nada de "aprenda os grupos
musculares" ou "entenda a fisiologia da hipertrofia" como missão própria).
Priorize: um plano de treino estruturado e progressivo, organização de
rotina (frequência, dias de descanso), orientação prática de alimentação
(não bioquímica) e, no máximo, alguma missão de medição/acompanhamento
(peso, medidas, fotos de progresso). Um conceito só vale virar missão
quando muda a execução na hora (ex: "o que é progressão de carga" pode
valer a pena porque a pessoa aplica isso todo treino); teoria que não leva
a nenhuma ação não deve virar missão.
""",
    "CAREER": """
Este objetivo é de CARREIRA. Inclua missões práticas de carreira (montar/
revisar currículo, LinkedIn, portfólio, prática de entrevista, networking)
-- mas SEM cortar o aprendizado técnico necessário para o objetivo: se a
pessoa quer "conseguir vaga de dados", ela ainda precisa aprender SQL/Python
de verdade, currículo bom não substitui competência real. Equilibre bem os
dois: normalmente os capítulos iniciais focam mais em construir a
habilidade em si, e os capítulos finais (mais perto de aplicar para vagas)
trazem as missões de currículo/entrevista/networking.
""",
    "FINANCE": """
Este objetivo é de FINANÇAS. Equilibre teoria e prática: conceitos
essenciais (ex: juros compostos, tipos de investimento, como funciona
determinado produto financeiro) valem a pena quando embasam uma decisão
real, mas sempre amarrados a uma ação concreta na sequência (montar
orçamento, abrir conta em corretora, categorizar gastos, definir reserva de
emergência). Evite teoria de economia que não leva a nenhuma decisão
prática.
""",
    "HABIT": """
Este objetivo é de HÁBITO. O foco é execução e consistência, não teoria
sobre por que o hábito é bom. Priorize missões de ação direta (fazer a
coisa, registrar, ajustar o ambiente/gatilhos que causam o comportamento) e
evite missões puramente conceituais/explicativas.
""",
}


class RoadmapFormatError(Exception):
    """Levantado quando o JSON devolvido pela IA não tem o formato esperado."""


class GenerateRoadmapUseCase:
    """Gera o roadmap propriamente dito e persiste. Pressupõe que a
    moderação e a triagem inicial (IntakeGoalUseCase) já rodaram antes --
    quem enfileira este job (o handler "intake_goal") só faz isso depois de
    confirmar que o objetivo é seguro e tem informação suficiente. Ver
    app/core/jobs/handlers.py.

    Contrato importante: este caso de uso NUNCA deixa uma exceção escapar.
    Ele sempre termina atualizando o goal para um estado definitivo
    (completed | failed), porque quem o chama é uma tarefa em background —
    se uma exceção escapasse aqui, ninguém estaria "ouvindo" pra tratar o
    erro, e o goal ficaria preso em "pending" para sempre.
    """

    def __init__(
        self,
        goal_repository: GoalRepository,
        roadmap_repository: RoadmapRepository,
        recommendation_repository: RecommendationRepository,
        user_repository: UserRepository,
        ai_client: GeminiClient,
    ):
        self.goal_repository = goal_repository
        self.roadmap_repository = roadmap_repository
        self.recommendation_repository = recommendation_repository
        self.user_repository = user_repository
        self.ai_client = ai_client

    async def execute(self, goal_id: int) -> None:
        goal = await self.goal_repository.get_by_id(goal_id)
        if goal is None:
            return

        try:
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

            recommendations_data = result.get("recommendations")
            if isinstance(recommendations_data, list) and recommendations_data:
                await self.recommendation_repository.bulk_create(goal.id, recommendations_data[:6])

            await self.goal_repository.update(
                goal_id,
                title=result["title"],
                generation_status="completed",
                estimated_completion_weeks=self._extract_estimated_weeks(result),
            )

        except Exception as exc:  
            await self.goal_repository.rollback()
            await self.goal_repository.update(
                goal_id,
                generation_status="failed",
                generation_error=safe_error_message(exc, "Não foi possível gerar seu roadmap"),
            )
            await self.user_repository.refund_credits(goal.user_id, settings.CREDITS_COST_GENERATE_ROADMAP)

    @staticmethod
    def _build_generation_prompt(goal) -> str:
        effective_prompt = goal.improved_prompt or goal.context_prompt
        prompt = f"Objetivo do usuário:\n{wrap_user_text(effective_prompt)}"

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

        category_guidance = CATEGORY_GUIDANCE.get(goal.category)
        if category_guidance:
            prompt += f"\n{category_guidance}"

        return prompt

    @staticmethod
    def _extract_estimated_weeks(result: dict) -> "int | None":
        """Campo 'bônus', não crítico -- se a IA não trouxer ou trouxer algo
        que não é um número válido, seguimos sem quebrar a geração por causa
        disso (diferente de 'title'/'chapters', que são essenciais)."""
        value = result.get("estimated_completion_weeks")
        if isinstance(value, bool):  
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