from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import PaginationParams, get_current_user
from app.api.v1.schemas.flashcards import (
    AnswerFlashcardReviewRequest,
    AnswerFlashcardReviewResponse,
    ApproveCandidateRequest,
    FlashcardCreateRequest,
    FlashcardOut,
    FlashcardUpdateRequest,
)
from app.application.flashcards.answer_flashcard_review import (
    AnswerFlashcardReviewUseCase,
    FlashcardNotActiveError,
)
from app.application.flashcards.approve_candidate import ApproveCandidateUseCase, NotAPendingCandidateError
from app.application.flashcards.create_flashcard import CreateFlashcardUseCase
from app.application.flashcards.deck_access import DeckAccessDeniedError, DeckNotFoundError
from app.application.flashcards.delete_flashcard import DeleteFlashcardUseCase
from app.application.flashcards.flashcard_access import FlashcardAccessDeniedError, FlashcardNotFoundError
from app.application.flashcards.get_due_flashcards import GetDueFlashcardsUseCase
from app.application.flashcards.list_pending_candidates import ListPendingCandidatesUseCase
from app.application.flashcards.update_flashcard import UpdateFlashcardUseCase
from app.infrastructure.database.models import User
from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.deck_repository import SQLAlchemyDeckRepository
from app.infrastructure.repositories.flashcard_repository import SQLAlchemyFlashcardRepository

router = APIRouter()


@router.get("/pending", response_model=List[FlashcardOut])
async def list_pending_candidates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    pagination: PaginationParams = Depends(PaginationParams),
):
    """Candidatos que a extração de IA gerou (ver Task de extração,
    app/application/flashcards/extract_concepts.py), aguardando você
    escolher quais realmente quer no baralho -- aprove com POST
    /flashcards/{id}/approve, ou rejeite com DELETE /flashcards/{id}."""
    repository = SQLAlchemyFlashcardRepository(db)
    use_case = ListPendingCandidatesUseCase(repository)
    contexts = await use_case.execute(current_user.id, limit=pagination.limit, offset=pagination.offset)
    return [FlashcardOut.from_context(c) for c in contexts]


@router.get("/due", response_model=List[FlashcardOut])
async def get_due_flashcards(
    deck_id: Optional[int] = Query(None, description="Filtra por um baralho específico; sem isso, traz de todos."),
    goal_id: Optional[int] = Query(None, description="Filtra por flashcards originados deste objetivo."),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    pagination: PaginationParams = Depends(PaginationParams),
):
    """Respeita o teto diário (ver settings.DAILY_REVIEW_LIMIT): quando a
    conta já bateu o teto de hoje nesse escopo (deck_id/goal_id, ou geral
    se nenhum for informado), volta lista vazia -- o resto do que estiver
    atrasado aparece nos próximos dias, não tudo de uma vez."""
    flashcard_repository = SQLAlchemyFlashcardRepository(db)
    deck_repository = SQLAlchemyDeckRepository(db)
    use_case = GetDueFlashcardsUseCase(flashcard_repository, deck_repository)

    try:
        contexts = await use_case.execute(
            current_user.id,
            user_timezone=current_user.timezone,
            deck_id=deck_id,
            goal_id=goal_id,
            limit=pagination.limit,
            offset=pagination.offset,
        )
    except (DeckNotFoundError, DeckAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Baralho não encontrado.")

    return [FlashcardOut.from_context(c) for c in contexts]


@router.post("", response_model=FlashcardOut, status_code=status.HTTP_201_CREATED)
async def create_flashcard(
    payload: FlashcardCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Cria um flashcard escrito à mão -- sem passar por extração de IA
    nem por aprovação, entra direto ativo (ver CreateFlashcardUseCase)."""
    flashcard_repository = SQLAlchemyFlashcardRepository(db)
    deck_repository = SQLAlchemyDeckRepository(db)
    use_case = CreateFlashcardUseCase(flashcard_repository, deck_repository)

    try:
        return await use_case.execute(
            user_id=current_user.id, front=payload.front, back=payload.back, deck_id=payload.deck_id
        )
    except (DeckNotFoundError, DeckAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Baralho não encontrado.")


@router.patch("/{flashcard_id}", response_model=FlashcardOut)
async def update_flashcard(
    flashcard_id: int,
    payload: FlashcardUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    flashcard_repository = SQLAlchemyFlashcardRepository(db)
    deck_repository = SQLAlchemyDeckRepository(db)
    use_case = UpdateFlashcardUseCase(flashcard_repository, deck_repository)

    try:
        return await use_case.execute(
            flashcard_id=flashcard_id,
            user_id=current_user.id,
            front=payload.front,
            back=payload.back,
            deck_id=payload.deck_id,
        )
    except (FlashcardNotFoundError, FlashcardAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flashcard não encontrado.")
    except (DeckNotFoundError, DeckAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Baralho não encontrado.")


@router.delete("/{flashcard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flashcard(
    flashcard_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Apaga o flashcard de vez -- serve tanto pra rejeitar um candidato
    pendente quanto pra apagar um ativo ou já graduado."""
    repository = SQLAlchemyFlashcardRepository(db)
    use_case = DeleteFlashcardUseCase(repository)

    try:
        await use_case.execute(flashcard_id=flashcard_id, user_id=current_user.id)
    except (FlashcardNotFoundError, FlashcardAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flashcard não encontrado.")


@router.post("/{flashcard_id}/approve", response_model=FlashcardOut)
async def approve_candidate(
    flashcard_id: int,
    payload: ApproveCandidateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    flashcard_repository = SQLAlchemyFlashcardRepository(db)
    deck_repository = SQLAlchemyDeckRepository(db)
    use_case = ApproveCandidateUseCase(flashcard_repository, deck_repository)

    try:
        return await use_case.execute(flashcard_id=flashcard_id, user_id=current_user.id, deck_id=payload.deck_id)
    except (FlashcardNotFoundError, FlashcardAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flashcard não encontrado.")
    except (DeckNotFoundError, DeckAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Baralho não encontrado.")
    except NotAPendingCandidateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("/{flashcard_id}/review", response_model=AnswerFlashcardReviewResponse)
async def answer_flashcard_review(
    flashcard_id: int,
    payload: AnswerFlashcardReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    flashcard_repository = SQLAlchemyFlashcardRepository(db)
    deck_repository = SQLAlchemyDeckRepository(db)
    use_case = AnswerFlashcardReviewUseCase(flashcard_repository, deck_repository)

    try:
        result = await use_case.execute(
            flashcard_id=flashcard_id,
            user_id=current_user.id,
            rating=payload.rating,
            user_timezone=current_user.timezone,
        )
    except (FlashcardNotFoundError, FlashcardAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flashcard não encontrado.")
    except FlashcardNotActiveError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    return AnswerFlashcardReviewResponse(
        flashcard=result.flashcard,
        graduated=result.graduated,
        remaining_reviews_today=result.remaining_reviews_today,
        daily_bonus_awarded=result.daily_bonus_awarded,
        xp_earned=result.xp_earned,
    )
