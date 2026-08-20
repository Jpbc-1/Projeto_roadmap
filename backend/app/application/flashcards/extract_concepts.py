import logging
from typing import Any, Dict, List, Optional

from app.application.flashcards import scheduler
from app.application.knowledge.embedding_utils import find_duplicate_node
from app.core.ai.gemini_client import GeminiClient
from app.core.ai.prompt_safety import PROMPT_INJECTION_GUARD, wrap_user_text
from app.domain.repositories.deck_repository import DeckRepository
from app.domain.repositories.flashcard_repository import FlashcardRepository
from app.domain.repositories.goal_repository import GoalRepository
from app.domain.repositories.knowledge_node_repository import KnowledgeNodeRepository
from app.domain.repositories.roadmap_repository import RoadmapRepository

logger = logging.getLogger(__name__)

FLASHCARD_MIN_IMPORTANCE = 4

EXTRACTION_SYSTEM_INSTRUCTION = """
Você é a IA do Mapa do Conhecimento do Roadmap AI. Sua tarefa é olhar as
missões que o usuário acabou de concluir num capítulo, e identificar os
conceitos genuinamente CONCEITUAIS/TEÓRICOS que vale a pena registrar --
ignorando missões puramente práticas/de ação.

Você recebe uma lista de missões concluídas (título + descrição). Para cada
uma, julgue se ela representa CONHECIMENTO CONCEITUAL (fatos, teoria,
terminologia, técnica que precisa ser lembrada) ou uma AÇÃO PRÁTICA (uma
tarefa que, uma vez feita, não precisa ser "lembrada" da mesma forma -- ex:
"instale o Python", "monte seu currículo", "abra uma conta em uma
corretora", "aplique para 5 vagas").

Das missões conceituais, extraia no máximo 4 conceitos-chave NO TOTAL (não
por missão), usando SEMPRE o termo canônico/padrão mais comum para aquele
conceito (ex: "for loop", não "laço de repetição" nem "estrutura de
repetição for") -- isso ajuda a evitar duplicatas quando o mesmo conceito
aparecer de novo com outras palavras no futuro.

Para CADA conceito extraído, avalie também "importance" de 0 a 5 -- não é
sobre o quão difícil o conceito é, é sobre o quão CONVENIENTE seria a
pessoa revisar isso depois, espaçadamente, pra não esquecer:
- 5: pré-requisito essencial pro resto do aprendizado, ou algo que a
  pessoa claramente vai precisar usar muito dali pra frente.
- 4: importante, vale a pena fixar na memória de longo prazo.
- 3 ou menos: relevante pro capítulo, mas não crítico revisar depois
  (detalhe secundário, muito específico do contexto, ou algo que já vai
  ser naturalmente reforçado só de continuar praticando).

Quando importance for 4 ou 5 (E SÓ NESSE CASO), escreva também um
flashcard de verdade nos campos "front" e "back": "front" é uma pergunta
objetiva que testa se a pessoa lembra do conceito (evite perguntas do tipo
"o que é X" -- prefira perguntas que exigem aplicar, comparar ou explicar
com as próprias palavras), "back" é a resposta direta e curta (1-3
frases). Quando importance for menor que 4, deixe front e back como null
-- não vale a pena gastar texto com um flashcard que não vai ser usado.

Para CADA conceito, informe também "source_mission_number": o número (1,
2, 3...) da missão da lista abaixo de onde esse conceito veio -- use o
número da missão que mais diretamente originou o conceito. Se o conceito
realmente amarrar 2 ou mais missões de forma que não dá pra apontar uma só
com confiança, use null -- é melhor não indicar origem do que indicar
errado.

Se NENHUMA missão do capítulo for conceitual, devolva uma lista vazia --
não force conceitos que não existem só para preencher.

Responda SOMENTE em JSON, no formato do schema fornecido.
""" + PROMPT_INJECTION_GUARD

EXTRACTION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "concepts": {
            "type": "ARRAY",
            "maxItems": 4,
            "items": {
                "type": "OBJECT",
                "properties": {
                    "concept": {"type": "STRING"},
                    "importance": {"type": "INTEGER"},
                    "source_mission_number": {"type": "INTEGER", "nullable": True},
                    "front": {"type": "STRING", "nullable": True},
                    "back": {"type": "STRING", "nullable": True},
                },
                "required": ["concept", "importance", "source_mission_number", "front", "back"],
            },
        },
    },
    "required": ["concepts"],
}


class ExtractConceptsUseCase:
    """Substitui o antigo ExtractKnowledgeNodesUseCase -- mesmo gatilho
    (capítulo concluído, ver core/jobs/handlers.py), mas agora numa
    chamada de IA só: extrai o conceito, julga a importância E já escreve
    o flashcard (pergunta/resposta) quando vale a pena, em vez de duas
    chamadas separadas (extrair, depois gerar conteúdo) -- mais barato e
    mantém a IA que decidiu "isso importa" no mesmo contexto que escreve
    o flashcard, sem perder informação entre uma chamada e outra.

    Todo conceito extraído vira um KnowledgeNode (mantém o Mapa do
    Conhecimento completo e o dedup por embedding funcionando pra
    qualquer conceito, não só os importantes) -- mas só os com importance
    >= FLASHCARD_MIN_IMPORTANCE ganham um Flashcard, e mesmo esses nascem
    como "pending_review": aparecem em GET /flashcards/pending pra pessoa
    decidir se quer aquilo no baralho de verdade (ver ApproveCandidateUseCase),
    nunca entram direto."""

    def __init__(
        self,
        goal_repository: GoalRepository,
        roadmap_repository: RoadmapRepository,
        knowledge_node_repository: KnowledgeNodeRepository,
        flashcard_repository: FlashcardRepository,
        deck_repository: DeckRepository,
        extraction_ai_client: GeminiClient,
        embedding_ai_client: GeminiClient,
    ):
        self.goal_repository = goal_repository
        self.roadmap_repository = roadmap_repository
        self.knowledge_node_repository = knowledge_node_repository
        self.flashcard_repository = flashcard_repository
        self.deck_repository = deck_repository
        self.extraction_ai_client = extraction_ai_client
        self.embedding_ai_client = embedding_ai_client

    async def execute(self, goal_id: int, user_id: int, chapter_id: int) -> Optional[int]:
        """Retorna quantos flashcards CANDIDATOS novos foram criados
        (aguardando aprovação), ou None se não havia nada conceitual pra
        extrair (goal inexistente, sinal claramente negativo -- ver
        gates abaixo --, ou capítulo sem conceito extraído -- isso NÃO é
        falha, é resultado válido).

        Erro de verdade (API do Gemini, embedding, banco) sobe pra quem
        chamou -- mesmo raciocínio do use case que este substitui: o
        worker (core/jobs/handlers.py + worker.py) já sabe reverter,
        logar e tentar de novo com backoff. Engolir erro aqui esconderia
        isso, fazendo o job aparecer "completed" mesmo tendo falhado."""
        goal = await self.goal_repository.get_by_id(goal_id)
        if goal is None:
            return None

        if not goal.involves_learning:
            logger.info("Mapa do Conhecimento: goal %s não envolve aprendizado, pulando extração.", goal_id)
            return None

        all_missions = await self.roadmap_repository.get_missions_by_chapter(chapter_id)
        if not all_missions:
            return None

        if not any(mission.is_conceptual for mission in all_missions):
            logger.info("Mapa do Conhecimento: capítulo %s sem nenhuma missão conceitual, pulando IA.", chapter_id)
            return None

        concepts = await self._extract_concepts(goal, all_missions)
        if not concepts:
            logger.info("Mapa do Conhecimento: capítulo %s sem conceitos extraídos.", chapter_id)
            return None

        existing_nodes = await self.knowledge_node_repository.get_by_goal(goal_id)

        candidates_created = 0
        for concept in concepts:
            embedding = await self.embedding_ai_client.embed_text(concept["concept"])

            duplicate = find_duplicate_node(embedding, existing_nodes)
            if duplicate is not None:
                logger.info(
                    "Mapa do Conhecimento: '%s' já existe como '%s', não duplicando.",
                    concept["concept"],
                    duplicate.topic_name,
                )
                continue

            node = await self.knowledge_node_repository.create(
                goal_id=goal_id,
                user_id=user_id,
                mission_id=concept["mission_id"],
                topic_name=concept["concept"],
                embedding=embedding,
                importance_score=concept["importance"],
            )
            existing_nodes.append(node)

            if concept["importance"] >= FLASHCARD_MIN_IMPORTANCE and concept.get("front") and concept.get("back"):
                main_deck = await self.deck_repository.get_or_create_main(user_id)
                initial_state = scheduler.new_card_state()
                await self.flashcard_repository.create(
                    user_id=user_id,
                    deck_id=main_deck.id,
                    knowledge_node_id=node.id,
                    front=concept["front"],
                    back=concept["back"],
                    status="pending_review",
                    fsrs_state=initial_state.fsrs_state,
                    fsrs_step=initial_state.fsrs_step,
                    stability=initial_state.stability,
                    difficulty=initial_state.difficulty,
                    due=initial_state.due,
                )
                candidates_created += 1

        logger.info(
            "Mapa do Conhecimento: %s candidato(s) de flashcard novo(s) para o goal %s (capítulo %s).",
            candidates_created,
            goal_id,
            chapter_id,
        )
        return candidates_created

    async def _extract_concepts(self, goal, missions) -> List[Dict[str, Any]]:
        prompt = f"Objetivo: {wrap_user_text(goal.context_prompt)}\n\nMissões concluídas neste capítulo:"
        for number, mission in enumerate(missions, start=1):
            description = mission.description or "(sem descrição)"
            prompt += f"\n{number}. \"{mission.title}\": {description}"

        result = await self.extraction_ai_client.generate_json(
            prompt=prompt,
            system_instruction=EXTRACTION_SYSTEM_INSTRUCTION,
            response_schema=EXTRACTION_SCHEMA,
        )
        raw_concepts = result.get("concepts") if isinstance(result, dict) else None
        if not isinstance(raw_concepts, list):
            return []

        concepts = []
        for item in raw_concepts[:4]:
            if not isinstance(item, dict):
                continue
            concept_name = str(item.get("concept", "")).strip()
            if not concept_name:
                continue
            try:
                importance = int(item.get("importance", 0))
            except (TypeError, ValueError):
                importance = 0
            importance = max(0, min(5, importance))   

            mission_id = None
            try:
                number = int(item.get("source_mission_number"))
                if 1 <= number <= len(missions):
                    mission_id = missions[number - 1].id
            except (TypeError, ValueError):
                pass

            front = item.get("front")
            back = item.get("back")
            concepts.append({
                "concept": concept_name,
                "importance": importance,
                "mission_id": mission_id,
                "front": str(front).strip() if front else None,
                "back": str(back).strip() if back else None,
            })
        return concepts
