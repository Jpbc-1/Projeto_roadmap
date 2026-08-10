"""Worker da fila de tarefas: uma task asyncio que roda dentro do próprio
processo da API (iniciada no lifespan do FastAPI, ver main.py), fazendo
polling na tabela background_jobs. Sem Redis, sem Celery, sem processo
separado -- pro estágio atual do projeto, a durabilidade de ter os jobs no
Postgres (sobrevive a restart, tem retry com backoff, dá pra consultar
status) já resolve o problema real sem exigir infra nova.

Se um dia o volume justificar rodar workers em processos/máquinas
separadas, basta chamar _poll_loop() num script à parte -- a lógica de
claim usa "FOR UPDATE SKIP LOCKED", que já é seguro pra múltiplos workers
concorrentes."""

import asyncio
import logging

from app.core.config import settings
from app.core.error_sanitization import safe_error_message
from app.core.jobs.handlers import JOB_HANDLERS
from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.repositories.job_repository import SQLAlchemyJobRepository

logger = logging.getLogger(__name__)

_worker_task = None


async def _process_job(job_id: int) -> None:
    async with AsyncSessionLocal() as session:
        job_repository = SQLAlchemyJobRepository(session)
        job = await job_repository.get_by_id(job_id)
        if job is None:
            return

        handler = JOB_HANDLERS.get(job.job_type)
        try:
            if handler is None:
                raise ValueError(f"job_type desconhecido: {job.job_type!r}")
            await handler(session, job.payload)
        except Exception as exc:  
            await session.rollback()
            error_message = safe_error_message(exc, f"Job #{job.id} ({job.job_type}) falhou")
            await job_repository.mark_failed_or_retry(job.id, error=error_message)
            return

        await job_repository.mark_completed(job.id)


async def _poll_loop() -> None:
    logger.info(
        "Worker de background jobs iniciado (poll a cada %.1fs, lote de %s).",
        settings.JOB_POLL_INTERVAL_SECONDS,
        settings.JOB_BATCH_SIZE,
    )
    while True:
        try:
            async with AsyncSessionLocal() as session:
                job_repository = SQLAlchemyJobRepository(session)
                jobs = await job_repository.claim_next_jobs(
                    limit=settings.JOB_BATCH_SIZE,
                    stale_after_seconds=settings.JOB_STALE_AFTER_SECONDS,
                )

            if jobs:
                results = await asyncio.gather(
                    *(_process_job(job.id) for job in jobs), return_exceptions=True
                )
                for job, result in zip(jobs, results):
                    if isinstance(result, Exception):
                        logger.exception("Job #%s: falha fora do tratamento normal", job.id, exc_info=result)
        except asyncio.CancelledError:
            raise
        except Exception:  
            logger.exception("Worker: falha inesperada no loop de polling.")

        await asyncio.sleep(settings.JOB_POLL_INTERVAL_SECONDS)


def start_worker() -> None:
    """Chamado no startup do FastAPI -- sobe o loop como uma task do
    próprio event loop da aplicação."""
    global _worker_task
    _worker_task = asyncio.create_task(_poll_loop())


async def stop_worker() -> None:
    """Chamado no shutdown -- cancela o loop de forma limpa em vez de
    deixar a task solta quando o processo encerra."""
    global _worker_task
    if _worker_task is not None:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass
        _worker_task = None
