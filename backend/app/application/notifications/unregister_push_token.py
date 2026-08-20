from app.domain.repositories.user_push_token_repository import UserPushTokenRepository


class UnregisterPushTokenUseCase:
    """Desvincula esse token do usuário atual. Idempotente de propósito:
    não levanta erro se o token já não existir, ou já não pertencer mais
    a esse usuário -- o endpoint (ver endpoints/notifications.py) sempre
    devolve 204, mesmo chamado duas vezes seguidas pro mesmo token."""

    def __init__(self, repository: UserPushTokenRepository):
        self.repository = repository

    async def execute(self, user_id: int, push_token: str) -> None:
        await self.repository.delete_for_user(user_id=user_id, push_token=push_token)
