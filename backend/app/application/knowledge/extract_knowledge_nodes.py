import logging
from datetime import date, timedelta
from typing import List, Optional

from app.application.knowledge.embedding_utils import find_duplicate_node
from app.core.ai.gemini_client import GeminiClient
from app.domain.repositories.goal_repository import GoalRepository
from app.domain.repositories.knowledge_node_repository import KnowledgeNodeRepository
from app.domain.repositories.roadmap_repository import RoadmapRepository

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_INSTRUCTION = """
Você é a IA do Mapa do Conhecimento do Roadmap AI. Sua tarefa é olhar as
missões que o usuário acabou de concluir num capítulo, e extrair os
conceitos genuinamente CONCEITUAIS/TEÓRICOS que valem revisão espaçada
depois -- ignorando missões puramente práticas/de ação.

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

Se NENHUMA missão do capítulo for conceitual, devolva uma lista vazia --
não force conceitos que não existem só para preencher.

Responda SOMENTE em JSON: {"concepts": ["conceito 1", "conceito 2"]}
"""

EXTRACTION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "concepts": {
            "type": "ARRAY",
            "maxItems": 4,
            "items": {"type": "STRING"},
        },
    },
    "required": ["concepts"],
}


class ExtractKnowledgeNodesUseCase:
    def __init__(
        self,
        goal_repository: GoalRepository,
        roadmap_repository: RoadmapRepository,
        knowledge_node_repository: KnowledgeNodeRepository,
        extraction_ai_client: GeminiClient,
        embedding_ai_client: GeminiClient,
    ):
        self.goal_repository = goal_repository
        self.roadmap_repository = roadmap_repository
        self.knowledge_node_repository = knowledge_node_repository
        self.extraction_ai_client = extraction_ai_client
        self.embedding_ai_client = embedding_ai_client

    async def execute(self, goal_id: int, user_id: int, chapter_id: int) -> Optional[int]:
        """Retorna quantos nós novos foram criados, ou None se nada foi
        feito (goal não envolve aprendizado, nada conceitual no capítulo,
        ou algo falhou). NUNCA deixa uma exceção escapar -- roda em
        background, sem ninguém "ouvindo" pra tratar erro."""
        try:
            goal = await self.goal_repository.get_by_id(goal_id)
            if goal is None or not goal.involves_learning:
                return None

            all_missions = await self.roadmap_repository.get_missions_by_chapter(chapter_id)
            missions = [m for m in all_missions if m.is_conceptual]
            if not missions:
                logger.info(
                    "Knowledge map: capítulo %s sem missões conceituais (só prática/setup), pulando IA.",
                    chapter_id,
                )
                return None

            concepts = await self._extract_concepts(goal, missions)
            if not concepts:
                logger.info("Knowledge map: capítulo %s sem conceitos conceituais.", chapter_id)
                return None

            existing_nodes = await self.knowledge_node_repository.get_by_goal(goal_id)

            created_count = 0
            for concept_name in concepts:
                embedding = await self.embedding_ai_client.embed_text(concept_name)

                duplicate = find_duplicate_node(embedding, existing_nodes)
                if duplicate is not None:
                    logger.info(
                        "Knowledge map: '%s' já existe como '%s', não duplicando.",
                        concept_name,
                        duplicate.topic_name,
                    )
                    continue

                node = await self.knowledge_node_repository.create(
                    goal_id=goal_id,
                    user_id=user_id,
                    topic_name=concept_name,
                    embedding=embedding,
                    next_review_date=date.today() + timedelta(days=1),
                )
                existing_nodes.append(node)  
                created_count += 1

            logger.info(
                "Knowledge map: %s conceito(s) novo(s) para o goal %s (capítulo %s).",
                created_count,
                goal_id,
                chapter_id,
            )
            return created_count

        except Exception: 
            logger.exception("Knowledge map: falha ao extrair conceitos do capítulo %s", chapter_id)
            return None

    async def _extract_concepts(self, goal, missions) -> List[str]:
        prompt = f"Objetivo: {goal.context_prompt}\n\nMissões concluídas neste capítulo:"
        for mission in missions:
            description = mission.description or "(sem descrição)"
            prompt += f"\n- \"{mission.title}\": {description}"

        result = await self.extraction_ai_client.generate_json(
            prompt=prompt,
            system_instruction=EXTRACTION_SYSTEM_INSTRUCTION,
            response_schema=EXTRACTION_SCHEMA,
        )
        concepts = result.get("concepts") if isinstance(result, dict) else None
        if not isinstance(concepts, list):
            return []
        return [str(c).strip() for c in concepts if str(c).strip()][:4]