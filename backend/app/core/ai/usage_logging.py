"""Telemetria de uso de token de IA -- não decide nada sobre créditos
(isso é app/core/ai/credits.py), só registra quanto token cada AÇÃO de
negócio realmente consome, pra calibrar os custos em créditos com dado
real antes do lançamento (ver User.credits_remaining e CREDITS_COST_* em
config.py)."""

from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import AIUsageLog


class UsageCollector:
    """Acumula uso de token EM MEMÓRIA (não escreve no banco a cada
    chamada) e só grava tudo de uma vez com flush(). Isso importa porque um
    GeminiClient pode ter várias chamadas concorrentes na mesma requisição
    (ex: asyncio.gather em adapt_roadmap.py, gerando o capítulo imediato e
    os capítulos futuros ao mesmo tempo) -- escrever direto no banco a cada
    callback exigiria usar a mesma AsyncSession de múltiplas corrotinas ao
    mesmo tempo, o que o SQLAlchemy não suporta. Uma lista Python comum,
    por outro lado, é segura contra isso (o event loop nunca interrompe um
    list.append() no meio)."""

    def __init__(self, user_id: Optional[int]):
        self.user_id = user_id
        self.records: List[Dict[str, Any]] = []

    def logger_for(self, action: str):
        """Devolve um callback pra passar como on_usage= na construção de
        um GeminiClient, já rotulado com o nome da ação de negócio (ex:
        "generate_roadmap", "moderation") -- o mesmo UsageCollector pode
        alimentar vários GeminiClient com ações diferentes numa mesma
        requisição/job."""

        async def _log(model: str, usage: Dict[str, Any]) -> None:
            self.records.append(
                {
                    "action": action,
                    "model": model,
                    "prompt_tokens": usage.get("promptTokenCount") or 0,
                    "completion_tokens": usage.get("candidatesTokenCount") or 0,
                    "total_tokens": usage.get("totalTokenCount") or 0,
                }
            )

        return _log

    async def flush(self, session: AsyncSession) -> None:
        """Grava tudo que foi acumulado até aqui, numa única transação.
        Chamar depois que todas as chamadas de IA concorrentes da
        requisição/job já terminaram (nunca no meio de um
        asyncio.gather)."""
        if not self.records:
            return
        for record in self.records:
            session.add(AIUsageLog(user_id=self.user_id, **record))
        await session.commit()
