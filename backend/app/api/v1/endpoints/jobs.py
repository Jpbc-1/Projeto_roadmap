from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.jobs import JobOut
from app.infrastructure.database.models import User
from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.job_repository import SQLAlchemyJobRepository

router = APIRouter()


@router.get("/{job_id}", response_model=JobOut)
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Consulta o status de qualquer job (geração de roadmap, auto-adapt,
    extração de conhecimento) -- o front pode dar poll aqui em vez de
    inferir status por efeitos colaterais em outras rotas."""
    job_repository = SQLAlchemyJobRepository(db)
    job = await job_repository.get_by_id(job_id)

    # 404 em vez de 403 quando o job é de outro usuário -- não confirma pra
    # quem está tentando adivinhar IDs que aquele job sequer existe.
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarefa não encontrada.")

    return job
