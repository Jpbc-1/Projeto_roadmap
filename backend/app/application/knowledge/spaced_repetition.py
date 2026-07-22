from typing import Tuple


QUALITY_MAP = {"again": 1, "hard": 3, "good": 4, "easy": 5}


def apply_sm2(
    quality: int,
    easiness_factor: float,
    interval_days: int,
    repetition_count: int,
) -> Tuple[int, float, int]:
    """Implementação do algoritmo SM-2 (SuperMemo 2) de repetição espaçada.

    Retorna (novo_interval_days, novo_easiness_factor, novo_repetition_count).

    - quality < 3 ("Errei"/"Difícil" abaixo do limiar): reseta a sequência,
      próxima revisão amanhã.
    - quality >= 3: avança a sequência (1 dia -> 6 dias -> intervalo anterior
      * fator de facilidade).
    - O fator de facilidade sempre se ajusta, mesmo em caso de erro, mas
      nunca cai abaixo de 1.3 (piso do algoritmo original).
    """
    new_easiness_factor = easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_easiness_factor = max(new_easiness_factor, 1.3)

    if quality < 3:
        return 1, new_easiness_factor, 0

    new_repetition_count = repetition_count + 1
    if new_repetition_count == 1:
        new_interval = 1
    elif new_repetition_count == 2:
        new_interval = 6
    else:
        new_interval = round(interval_days * new_easiness_factor)

    return new_interval, new_easiness_factor, new_repetition_count


def compute_mastery_level(interval_days: int) -> str:
    """Nível de domínio DERIVADO do intervalo atual -- não é guardado no
    banco, é calculado na leitura (fonte única de verdade: o intervalo)."""
    if interval_days < 7:
        return "BEGINNER"
    if interval_days < 30:
        return "INTERMEDIATE"
    return "MASTERED"