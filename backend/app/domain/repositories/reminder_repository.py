from datetime import datetime, time
from typing import Any, List, Optional, Protocol

from app.infrastructure.database.models import Reminder


class ReminderRepository(Protocol):
    async def create(
        self,
        user_id: int,
        label: str,
        time_of_day: time,
        days_of_week: List[int],
        notification_timing_mode: str = "app_default",
        notification_style: str = "app_generated",
        custom_message: Optional[str] = None,
    ) -> Reminder: ...

    async def list_by_user(self, user_id: int, limit: int, offset: int) -> List[Reminder]: ...

    async def get_by_id(self, reminder_id: int) -> Optional[Reminder]: ...

    async def update(self, reminder_id: int, **fields: Any) -> Reminder: ...

    async def delete(self, reminder_id: int) -> None: ...

    async def list_due(self, now_utc: datetime) -> List[Reminder]:
        """Lembretes ativos cujo dia da semana + horário já passaram (no
        fuso do DONO -- ver User.timezone) e que ainda não dispararam hoje
        (last_dispatched_date). Não precisa de janela de tempo nem
        checkpoint em memória: "ainda não disparei hoje" já é
        naturalmente à prova de ciclo atrasado ou processo reiniciado --
        cobre desde 1 segundo até vários dias de atraso igual. Usado pelo
        agendador de disparo, não pela tela."""
        ...

    async def try_claim_dispatch(self, reminder_id: int) -> bool:
        """UPDATE atômico condicional: só marca last_dispatched_date=hoje
        (calculado sozinho, no fuso do dono -- não recebe a data de fora)
        SE ainda não estava marcado pra hoje, e devolve True só pra quem
        ganhou a corrida. É isso -- não um lock distribuído nem Redis --
        que garante que múltiplas réplicas da API rodando o agendador ao
        mesmo tempo disparem cada lembrete UMA vez, não N vezes: a
        condição do WHERE só é satisfeita a primeira vez, então mesmo que
        duas réplicas cheguem aqui quase juntas, só a que COMMITAR
        primeiro tem linha afetada -- a segunda recebe 0 linhas e desiste
        (a primeira já cuidou disso). Ver docs/adr."""
        ...
