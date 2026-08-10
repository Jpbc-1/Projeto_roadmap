from typing import List, Optional, Protocol

from app.infrastructure.database.models import Achievement, UserAchievement


class AchievementRepository(Protocol):
    """
    Deliberadamente cross-domain (conta missão, capítulo E objetivo) em
    vez de espalhar um método de contagem em MissionRepository,
    RoadmapRepository e GoalRepository separados -- essa é a única
    consumidora dessas contagens agregadas por usuário, então faz mais
    sentido ela possuir as próprias queries do que inchar 3 repositórios
    que já existem com um método usado só daqui.
    """

    async def count_completed_missions(self, user_id: int) -> int: ...

    async def count_completed_chapters(self, user_id: int) -> int: ...

    async def count_completed_goals(self, user_id: int) -> int: ...

    async def get_by_condition(self, required_condition: str) -> Optional[Achievement]: ...

    async def has_unlocked(self, user_id: int, achievement_id: int) -> bool: ...

    async def unlock(self, user_id: int, achievement_id: int) -> UserAchievement: ...

    async def list_all(self) -> List[Achievement]: ...

    async def list_unlocked_for_user(self, user_id: int) -> List[UserAchievement]: ...
