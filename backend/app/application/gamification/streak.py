from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional


@dataclass
class StreakUpdate:
    new_total_xp: int
    new_level: int
    new_current_streak: int
    new_max_streak: int
    activity_date: date


def calculate_level(total_xp: int) -> int:
    """Fórmula simples: a cada 100 XP, sobe 1 nível."""
    return 1 + total_xp // 100


def calculate_streak_update(current_stats: Optional[object], xp_to_add: int, today: date) -> StreakUpdate:
    """Decide XP total, streak atual/máximo e nível, com base no histórico
    de atividade do usuário. Compartilhado entre qualquer ação que gere XP
    (concluir missão, terminar o bloco de revisões do dia, etc.) -- uma
    fonte só de verdade pra essa conta, em vez de duplicada em cada lugar.

    'current_stats' precisa só ter os atributos total_xp, current_streak,
    max_streak, last_activity_date (aceita o UserStats real ou qualquer
    objeto/fake com esses campos, útil em testes).
    """
    if current_stats is None:
        return StreakUpdate(
            new_total_xp=xp_to_add,
            new_level=calculate_level(xp_to_add),
            new_current_streak=1,
            new_max_streak=1,
            activity_date=today,
        )

    if current_stats.last_activity_date == today:
        new_streak = current_stats.current_streak  # já ativo hoje, streak não muda
    elif current_stats.last_activity_date == today - timedelta(days=1):
        new_streak = current_stats.current_streak + 1  # ativo ontem -> streak continua
    else:
        new_streak = 1  # quebrou o streak -> recomeça

    new_total_xp = current_stats.total_xp + xp_to_add
    new_max_streak = max(current_stats.max_streak, new_streak)

    return StreakUpdate(
        new_total_xp=new_total_xp,
        new_level=calculate_level(new_total_xp),
        new_current_streak=new_streak,
        new_max_streak=new_max_streak,
        activity_date=today,
    )