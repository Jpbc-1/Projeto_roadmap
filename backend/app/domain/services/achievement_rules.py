"""
As condições de desbloqueio são PURAS e DETERMINÍSTICAS de propósito --
"a pessoa completou 7 dias seguidos" é uma contagem, não um julgamento.
Nunca deve ser a IA decidindo se um marco foi ganho (isso introduziria
não-determinismo numa coisa que tem resposta certa). Onde a IA pode
ajudar de verdade é personalizando o TEXTO de celebração depois de
desbloqueado -- mesmo padrão 'app_generated'/'custom_message' que já
existe pros lembretes (ver domain/services/notification_content.py) --
não implementado ainda aqui, é a evolução natural.

Cada string aqui tem que ter uma linha correspondente semeada na tabela
achievements.required_condition (ver a migração) -- se não tiver, a
condição é ignorada silenciosamente (ver CheckAchievementsUseCase), não
quebra nada, só não desbloqueia.
"""
from dataclasses import dataclass
from typing import List

MISSION_THRESHOLDS = [1, 10, 50, 100]
CHAPTER_THRESHOLDS = [1, 10]
STREAK_THRESHOLDS = [7, 30, 100]
GOAL_THRESHOLDS = [1]


@dataclass
class AchievementProgress:
    total_missions_completed: int
    total_chapters_completed: int
    total_goals_completed: int
    current_streak: int


def conditions_met_for(progress: AchievementProgress) -> List[str]:
    """Devolve TODAS as condições que o estado atual satisfaz -- inclui
    as que já foram desbloqueadas antes (ex: alguém com 50 missões
    também satisfaz missions_1 e missions_10). Quem chama filtra o que
    já foi desbloqueado (ver AchievementRepository.has_unlocked) -- essa
    função não sabe nada de histórico, só do estado atual."""
    met = []

    for n in MISSION_THRESHOLDS:
        if progress.total_missions_completed >= n:
            met.append(f"missions_{n}")

    for n in CHAPTER_THRESHOLDS:
        if progress.total_chapters_completed >= n:
            met.append(f"chapters_{n}")

    for n in STREAK_THRESHOLDS:
        if progress.current_streak >= n:
            met.append(f"streak_{n}")

    for n in GOAL_THRESHOLDS:
        if progress.total_goals_completed >= n:
            met.append(f"goals_{n}")

    return met
