from typing import Dict, List, Optional

from sqlalchemy import func, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import Deck, Flashcard


class SQLAlchemyDeckRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_main(self, user_id: int) -> Deck:
        """UPSERT atômico no índice único parcial (user_id WHERE
        is_main=true) -- mesmo raciocínio de SQLAlchemyUserPushTokenRepository
        .upsert: um SELECT-depois-decide ingênuo tem uma corrida real aqui
        (2 requisições concorrentes criando o baralho principal na
        primeira vez que a conta usa a área de revisões -- ex: aprovar um
        candidato e criar um flashcard manual ao mesmo tempo -- ambas
        veriam "não existe" e bateriam no índice único uma da outra).

        set_={"name": Deck.name} é um no-op update de propósito: só existe
        pra fazer o RETURNING funcionar mesmo quando cai no conflito (sem
        DO UPDATE, ON CONFLICT DO NOTHING não devolve a linha existente)."""
        stmt = (
            pg_insert(Deck)
            .values(user_id=user_id, name="Principal", is_main=True)
            .on_conflict_do_update(
                index_elements=[Deck.user_id],
                index_where=text("is_main = true"),
                set_={"name": Deck.name},
            )
            .returning(Deck)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def create(self, user_id: int, name: str) -> Deck:
        deck = Deck(user_id=user_id, name=name, is_main=False)
        self.session.add(deck)
        await self.session.commit()
        await self.session.refresh(deck)
        return deck

    async def get_by_id(self, deck_id: int) -> Optional[Deck]:
        return await self.session.get(Deck, deck_id)

    async def list_by_user(self, user_id: int) -> List[Deck]:
        result = await self.session.execute(
            select(Deck).where(Deck.user_id == user_id).order_by(Deck.is_main.desc(), Deck.created_at)
        )
        return list(result.scalars().all())

    async def count_flashcards_by_status(self, deck_id: int) -> Dict[str, int]:
        result = await self.session.execute(
            select(Flashcard.status, func.count())
            .where(Flashcard.deck_id == deck_id)
            .group_by(Flashcard.status)
        )
        return {status: count for status, count in result.all()}

    async def move_flashcards_and_delete(self, deck_id: int, target_deck_id: int) -> None:
        await self.session.execute(
            update(Flashcard).where(Flashcard.deck_id == deck_id).values(deck_id=target_deck_id)
        )
        deck = await self.session.get(Deck, deck_id)
        if deck is not None:
            await self.session.delete(deck)
        await self.session.commit()
