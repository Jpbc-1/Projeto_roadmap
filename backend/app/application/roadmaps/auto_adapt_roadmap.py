from typing import Dict, List, Optional

from app.application.roadmaps.adapt_roadmap import AdaptRoadmapUseCase
from app.core.ai.gemini_client import GeminiClient
from app.domain.repositories.roadmap_repository import RoadmapRepository

TRIAGE_SYSTEM_INSTRUCTION = """
Você é um triador rápido de ritmo de aprendizado. Sua ÚNICA tarefa é ler
reflexões recentes que um usuário deixou sobre capítulos que acabou de
concluir, e decidir se vale a pena adaptar o roadmap dele agora.

Marque needs_adaptation como true SOMENTE se houver um sinal claro nas
reflexões: satisfação/facilidade excessiva repetida (sugerindo acelerar),
ou dificuldade/cansaço/frustração (sugerindo desacelerar).

Marque needs_adaptation como false se as reflexões forem neutras, vagas,
ausentes, mistas sem padrão claro, ou indicarem que o ritmo atual está bom.
Não adapte por qualquer motivo pequeno -- só quando o sinal for real.

Responda SOMENTE em JSON, neste formato:
{"needs_adaptation": true ou false, "direction": "accelerate" ou "slow_down" ou "none", "reason": "explicação curta"}
"""

TRIAGE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "needs_adaptation": {"type": "BOOLEAN"},
        "direction": {"type": "STRING"},
        "reason": {"type": "STRING"},
    },
    "required": ["needs_adaptation", "direction", "reason"],
}


class AutoAdaptRoadmapUseCase:
    def __init__(
        self,
        roadmap_repository: RoadmapRepository,
        triage_ai_client: GeminiClient,
        adapt_use_case: AdaptRoadmapUseCase,
        chapters_window: int = 2,
    ):
        self.roadmap_repository = roadmap_repository
        self.triage_ai_client = triage_ai_client
        self.adapt_use_case = adapt_use_case
        self.chapters_window = chapters_window

    async def execute(self, goal_id: int, user_id: int, roadmap_id: int) -> Optional[int]:
        """Retorna None se decidiu não adaptar (nada mudou), ou a quantidade
        de itens alterados se a adaptação completa foi acionada."""
        recent_chapter_ids = await self._get_recent_completed_chapter_ids(roadmap_id)
        if not recent_chapter_ids:
            return None

        reflections = await self.roadmap_repository.get_reflections_for_chapters(
            recent_chapter_ids, user_id
        )
        if not reflections:
            # Sem nenhuma reflexão registrada -> nem vale gastar a chamada
            # barata de triagem, não há nada pra ela analisar.
            return None

        decision = await self._triage(reflections)
        if not decision.get("needs_adaptation"):
            return None

        feedback = f"[Adaptação automática] {decision.get('reason', 'sinal detectado nas reflexões')}"
        return await self.adapt_use_case.execute(goal_id=goal_id, user_id=user_id, feedback=feedback)

    async def _get_recent_completed_chapter_ids(self, roadmap_id: int) -> List[int]:
        chapters = await self.roadmap_repository.get_chapters_by_roadmap(roadmap_id)
        completed = sorted(
            (c for c in chapters if c.status == "completed"),
            key=lambda c: c.order_index,
        )
        return [c.id for c in completed[-self.chapters_window :]]

    async def _triage(self, reflections: List[Dict[str, str]]) -> dict:
        prompt = "Reflexões recentes do usuário:\n"
        for item in reflections:
            prompt += f"- \"{item['mission_title']}\": {item['reflection']}\n"

        return await self.triage_ai_client.generate_json(
            prompt=prompt,
            system_instruction=TRIAGE_SYSTEM_INSTRUCTION,
            response_schema=TRIAGE_SCHEMA,
        )