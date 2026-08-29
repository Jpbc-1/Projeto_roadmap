from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol

from app.infrastructure.database.models import BackgroundJob


class JobRepository(Protocol):
    async def enqueue(
        self,
        job_type: str,
        payload: Dict[str, Any],
        user_id: Optional[int] = None,
        max_attempts: int = 3,
    ) -> BackgroundJob:
        """Cria um job "pending" pra rodar assim que um worker tiver vaga."""
        ...

    async def get_by_id(self, job_id: int) -> Optional[BackgroundJob]: ...

    async def count_recent_by_type_and_user(self, user_id: int, job_type: str, since: datetime) -> int:
        """Quantos jobs deste tipo foram enfileirados para este usuário
        desde `since` -- usado como teto anti-abuso (settings.
        EXTRACT_CONCEPTS_MAX_PER_DAY) pra não deixar alguém completando
        capítulos em sequência rápida gerar uma chamada de IA paga (Gemini)
        por chapter_id sem limite algum. Janela rolante em UTC (não por
        fuso do usuário) de propósito: isto é controle de custo, não uma
        feature voltada pro usuário -- não precisa da mesma precisão de
        "meia-noite local" que o DAILY_REVIEW_LIMIT de flashcards tem."""
        ...

    async def claim_next_jobs(self, limit: int, stale_after_seconds: int) -> List[BackgroundJob]:
        """Reivindica até `limit` jobs pendentes e prontos pra rodar (marca
        como "processing"), e de quebra recupera jobs que ficaram
        "processing" por mais de `stale_after_seconds` (worker que caiu no
        meio do trabalho) de volta pra "pending"."""
        ...

    async def mark_completed(self, job_id: int) -> None: ...

    async def mark_failed_or_retry(self, job_id: int, error: str) -> None:
        """Incrementa attempts; se ainda não estourou max_attempts, volta
        pra "pending" com backoff exponencial em run_after -- senão marca
        "failed" definitivamente."""
        ...
