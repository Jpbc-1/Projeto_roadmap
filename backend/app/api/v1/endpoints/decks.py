from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import PaginationParams, get_current_user
from app.api.v1.schemas.decks import DeckCreateRequest, DeckOut
from app.api.v1.schemas.flashcards import FlashcardOut
from app.application.flashcards.create_deck import CreateDeckUseCase
from app.application.flashcards.deck_access import DeckAccessDeniedError, DeckNotFoundError
from app.application.flashcards.delete_deck import CannotDeleteMainDeckError, DeleteDeckUseCase
from app.application.flashcards.list_decks import ListDecksUseCase
from app.application.flashcards.list_flashcards_by_deck import ListFlashcardsByDeckUseCase
from app.infrastructure.database.models import User
from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.deck_repository import SQLAlchemyDeckRepository
from app.infrastructure.repositories.flashcard_repository import SQLAlchemyFlashcardRepository

router = APIRouter()


@router.get("", response_model=List[DeckOut])
async def list_decks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """O baralho Principal aparece sempre, mesmo pra quem nunca usou a
    área de revisões ainda (ver ListDecksUseCase)."""
    repository = SQLAlchemyDeckRepository(db)
    use_case = ListDecksUseCase(repository)
    summaries = await use_case.execute(current_user.id)
    return [
        DeckOut(
            id=summary.deck.id,
            name=summary.deck.name,
            is_main=summary.deck.is_main,
            active_count=summary.active_count,
            pending_count=summary.pending_count,
            graduated_count=summary.graduated_count,
        )
        for summary in summaries
    ]


@router.post("", response_model=DeckOut, status_code=status.HTTP_201_CREATED)
async def create_deck(
    payload: DeckCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repository = SQLAlchemyDeckRepository(db)
    use_case = CreateDeckUseCase(repository)
    deck = await use_case.execute(user_id=current_user.id, name=payload.name)
    return DeckOut(id=deck.id, name=deck.name, is_main=deck.is_main, active_count=0, pending_count=0, graduated_count=0)


@router.delete("/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deck(
    deck_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Apaga o baralho -- os flashcards dele são movidos pro Principal
    antes, nunca apagados junto (ver DeleteDeckUseCase). O Principal em si
    não pode ser apagado."""
    repository = SQLAlchemyDeckRepository(db)
    use_case = DeleteDeckUseCase(repository)

    try:
        await use_case.execute(deck_id=deck_id, user_id=current_user.id)
    except (DeckNotFoundError, DeckAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Baralho não encontrado.")
    except CannotDeleteMainDeckError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{deck_id}/flashcards", response_model=List[FlashcardOut])
async def list_flashcards_by_deck(
    deck_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    pagination: PaginationParams = Depends(PaginationParams),
):
    flashcard_repository = SQLAlchemyFlashcardRepository(db)
    deck_repository = SQLAlchemyDeckRepository(db)
    use_case = ListFlashcardsByDeckUseCase(flashcard_repository, deck_repository)

    try:
        contexts = await use_case.execute(
            deck_id=deck_id, user_id=current_user.id, limit=pagination.limit, offset=pagination.offset
        )
    except (DeckNotFoundError, DeckAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Baralho não encontrado.")

    return [FlashcardOut.from_context(c) for c in contexts]
