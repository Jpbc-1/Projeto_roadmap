from typing import List, Protocol

from app.infrastructure.database.models import UserPushToken


class UserPushTokenRepository(Protocol):
    async def upsert(self, user_id: int, push_token: str, platform: str) -> UserPushToken:
        """Cria a linha se push_token é novo; se já existe, atualiza
        user_id/platform/updated_at (ver implementação SQLAlchemy pra o
        motivo de isso precisar ser um UPSERT atômico no banco, não um
        SELECT-depois-decide em Python)."""
        ...

    async def delete_for_user(self, user_id: int, push_token: str) -> None:
        """Remove o token SE ele pertencer a esse user_id. Não faz nada
        (sem erro) se o token não existir ou pertencer a outro usuário --
        idempotente de propósito, ver UnregisterPushTokenUseCase."""
        ...

    async def list_by_user_id(self, user_id: int) -> List[UserPushToken]:
        """Todos os aparelhos registrados desse usuário -- usado pelo
        handler de disparo (core/jobs/handlers.py) pra mandar a
        notificação pra todos eles, não só o mais recente."""
        ...

    async def delete_by_tokens(self, push_tokens: List[str]) -> None:
        """Apaga em lote pelos valores de push_token (não por id nem por
        user_id) -- usado quando o Expo confirma DeviceNotRegistered pra
        um ou mais tokens durante o envio."""
        ...
