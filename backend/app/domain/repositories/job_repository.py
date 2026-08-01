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
