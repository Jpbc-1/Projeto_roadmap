from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import BackgroundJob


class SQLAlchemyJobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def enqueue(
        self,
        job_type: str,
        payload: Dict[str, Any],
        user_id: Optional[int] = None,
        max_attempts: int = 3,
    ) -> BackgroundJob:
        job = BackgroundJob(
            job_type=job_type,
            payload=payload,
            status="pending",
            max_attempts=max_attempts,
            user_id=user_id,
        )
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_by_id(self, job_id: int) -> Optional[BackgroundJob]:
        return await self.session.get(BackgroundJob, job_id)

    async def claim_next_jobs(self, limit: int, stale_after_seconds: int) -> List[BackgroundJob]:
        now = datetime.now(timezone.utc)
        stale_threshold = now - timedelta(seconds=stale_after_seconds)

        # Jobs que travaram em "processing" (worker morreu no meio) voltam
        # pra fila -- sem isso, um crash no meio de um job o deixaria preso
        # "em andamento" pra sempre, invisível pro próximo poll.
        await self.session.execute(
            update(BackgroundJob)
            .where(BackgroundJob.status == "processing", BackgroundJob.locked_at < stale_threshold)
            .values(status="pending", run_after=now)
        )
        await self.session.commit()

        # FOR UPDATE SKIP LOCKED: seguro mesmo se um dia rodar mais de um
        # worker/processo ao mesmo tempo -- cada um pega jobs diferentes em
        # vez de brigar pela mesma linha.
        result = await self.session.execute(
            select(BackgroundJob)
            .where(BackgroundJob.status == "pending", BackgroundJob.run_after <= now)
            .order_by(BackgroundJob.run_after)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        jobs = list(result.scalars().all())
        for job in jobs:
            job.status = "processing"
            job.locked_at = now
        await self.session.commit()
        return jobs

    async def mark_completed(self, job_id: int) -> None:
        await self.session.execute(
            update(BackgroundJob)
            .where(BackgroundJob.id == job_id)
            .values(status="completed", locked_at=None)
        )
        await self.session.commit()

    async def mark_failed_or_retry(self, job_id: int, error: str) -> None:
        job = await self.session.get(BackgroundJob, job_id)
        if job is None:
            return

        job.attempts += 1
        job.last_error = error[:2000]

        if job.attempts >= job.max_attempts:
            job.status = "failed"
            job.locked_at = None
        else:
            backoff_seconds = min(30 * (2 ** job.attempts), 3600)
            job.status = "pending"
            job.run_after = datetime.now(timezone.utc) + timedelta(seconds=backoff_seconds)
            job.locked_at = None

        await self.session.commit()
