from app.domain.repositories.user_push_token_repository import UserPushTokenRepository
from app.infrastructure.database.models import UserPushToken


class RegisterPushTokenUseCase:
    """Registra (ou re-vincula, se o token já existia em outra conta ou
    já era desse mesmo usuário) o push token de um aparelho ao usuário
    atual.

    A regra de negócio inteira -- UPSERT por push_token, não por user_id
    -- vive na escolha do método do repositório chamado aqui, não neste
    use case nem no endpoint (ver SQLAlchemyUserPushTokenRepository.upsert
    pro motivo de isso ser um UPSERT atômico no banco)."""

    def __init__(self, repository: UserPushTokenRepository):
        self.repository = repository

    async def execute(self, user_id: int, push_token: str, platform: str) -> UserPushToken:
        return await self.repository.upsert(user_id=user_id, push_token=push_token, platform=platform)
