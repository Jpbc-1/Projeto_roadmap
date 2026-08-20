"""Wrapper fino em volta da lib fsrs (PyPI, mantida pela Open Spaced
Repetition -- mesmos autores do algoritmo, https://pypi.org/project/fsrs/)
em vez de reimplementar a matemática do FSRS na mão: é um algoritmo com
dezenas de constantes calibradas em ~700M revisões reais, fácil de errar
sutilmente reproduzindo à mão, então usamos a biblioteca de referência.

Este módulo só conhece tipos primitivos (str/float/int/datetime), nunca o
model Flashcard do SQLAlchemy -- fica testável isoladamente, e quem
persiste o resultado (repository) decide como isso vira colunas."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import fsrs

_SCHEDULER = fsrs.Scheduler(learning_steps=(), relearning_steps=())

_STATE_TO_DB = {fsrs.State.Learning: "learning", fsrs.State.Review: "review", fsrs.State.Relearning: "relearning"}
_DB_TO_STATE = {value: key for key, value in _STATE_TO_DB.items()}

RATING_TO_FSRS = {
    "again": fsrs.Rating.Again,
    "hard": fsrs.Rating.Hard,
    "good": fsrs.Rating.Good,
    "easy": fsrs.Rating.Easy,
}


@dataclass
class SchedulingResult:
    fsrs_state: str
    fsrs_step: Optional[int]
    stability: Optional[float]
    difficulty: Optional[float]
    due: datetime
    elapsed_days: Optional[int]


def new_card_state() -> SchedulingResult:
    """Estado inicial de um flashcard que nunca foi revisado -- due vem
    "agora" (fsrs.Card() sem argumentos já calcula isso sozinho), então o
    cartão fica disponível pra primeira revisão assim que for aprovado/
    criado, sem esperar nenhum dia."""
    card = fsrs.Card()
    return SchedulingResult(
        fsrs_state=_STATE_TO_DB[card.state],
        fsrs_step=card.step,
        stability=card.stability,
        difficulty=card.difficulty,
        due=card.due,
        elapsed_days=None,
    )


def schedule_review(
    *,
    fsrs_state: str,
    fsrs_step: Optional[int],
    stability: Optional[float],
    difficulty: Optional[float],
    due: datetime,
    last_review_at: Optional[datetime],
    rating: str,
    review_datetime: Optional[datetime] = None,
) -> SchedulingResult:
    """Aplica uma resposta ("again"/"hard"/"good"/"easy") ao estado atual
    do cartão e devolve o novo estado -- não persiste nada, quem chama
    decide isso (ver AnswerFlashcardReviewUseCase)."""
    review_datetime = review_datetime or datetime.now(timezone.utc)

    card = fsrs.Card(
        state=_DB_TO_STATE[fsrs_state],
        step=fsrs_step,
        stability=stability,
        difficulty=difficulty,
        due=due,
        last_review=last_review_at,
    )

    elapsed_days = (review_datetime - last_review_at).days if last_review_at else None

    new_card, _review_log = _SCHEDULER.review_card(card, RATING_TO_FSRS[rating], review_datetime=review_datetime)

    return SchedulingResult(
        fsrs_state=_STATE_TO_DB[new_card.state],
        fsrs_step=new_card.step,
        stability=new_card.stability,
        difficulty=new_card.difficulty,
        due=new_card.due,
        elapsed_days=elapsed_days,
    )
