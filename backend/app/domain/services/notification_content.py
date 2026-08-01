"""
Resolve o TEXTO de verdade que vai numa notificação -- separado do CRUD
de propósito, porque essa é a única parte que muda dependendo do que
está pendente no momento do disparo (não dá pra guardar o texto de
app_generated no banco, ele precisa ser calculado na hora do envio).

Quem chama isso é o handler de disparo (app/core/jobs/handlers.py), não
os casos de uso de CRUD.
"""
from dataclasses import dataclass
from typing import Optional

from app.infrastructure.database.models import CalendarEvent, Reminder


@dataclass
class NotificationContent:
    title: str
    body: str


def resolve_reminder_content(
    reminder: Reminder, pending_mission_title: Optional[str] = None
) -> NotificationContent:
    """pending_mission_title: título da missão pendente de hoje, se houver
    -- quem descobre isso é quem chama (o handler), não este serviço, pra
    não misturar o domínio de Reminder com o de Mission aqui dentro."""
    if reminder.notification_style == "custom_message" and reminder.custom_message:
        return NotificationContent(title="Roadmap AI", body=reminder.custom_message)

    if pending_mission_title:
        return NotificationContent(
            title="Roadmap AI", body=f"{pending_mission_title} ainda está esperando por você."
        )

    return NotificationContent(title="Roadmap AI", body=reminder.label)


def resolve_calendar_event_content(event: CalendarEvent) -> NotificationContent:
    if event.notification_style == "custom_message" and event.custom_message:
        return NotificationContent(title="Roadmap AI", body=event.custom_message)

    if event.remind_before_minutes:
        return NotificationContent(
            title="Roadmap AI", body=f"{event.title} começa em {event.remind_before_minutes} minutos."
        )

    return NotificationContent(title="Roadmap AI", body=f"Lembrete: {event.title}")
