from typing import List

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import UserPushToken


class SQLAlchemyUserPushTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, user_id: int, push_token: str, platform: str) -> UserPushToken:
        """UPSERT atômico por push_token: INSERT ... ON CONFLICT (push_token)
        DO UPDATE, em vez de "SELECT por token, depois decide INSERT ou
        UPDATE em Python" (o padrão usado em ex: login_with_oauth.py).

        Por quê aqui é diferente: duas requisições concorrentes pro MESMO
        token são um caso real, não só teórico -- o app pode chamar
        register-token de novo por retry de rede, ou o usuário pode trocar
        de conta rapidamente no mesmo aparelho. Num SELECT-depois-decide,
        as duas requisições veriam "não existe" e as duas tentariam INSERT;
        uma bateria na unique constraint de push_token e quebraria com
        IntegrityError (500 não tratado). ON CONFLICT resolve isso em uma
        única ida ao banco, sem essa janela de corrida.

        Se o token já existe (mesmo aparelho de novo, reinstalação, ou
        troca de usuário no mesmo device), user_id/platform/updated_at são
        sobrescritos -- é assim que o backend sabe pra quem mandar a
        próxima notificação nesse aparelho, sem lógica extra no app.
        """
        stmt = (
            pg_insert(UserPushToken)
            .values(user_id=user_id, push_token=push_token, platform=platform)
            .on_conflict_do_update(
                index_elements=[UserPushToken.push_token],
                set_={
                    "user_id": user_id,
                    "platform": platform,
                    "updated_at": func.now(),
                },
            )
            .returning(UserPushToken)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def delete_for_user(self, user_id: int, push_token: str) -> None:
        """Filtra por push_token E user_id -- não deixa uma conta apagar
        token de outra por engano (ex: o mesmo aparelho já foi re-registrado
        por outro usuário entre o logout e essa chamada de unregister).

        Não confere se a linha existia: DELETE sem WHERE match nenhuma
        linha e ainda assim comita com sucesso -- é isso que faz o
        endpoint poder devolver 204 sempre (ver UnregisterPushTokenUseCase
        e endpoints/notifications.py), idempotente por construção, sem
        precisar de um SELECT antes só pra decidir o status code.
        """
        await self.session.execute(
            delete(UserPushToken).where(
                UserPushToken.push_token == push_token,
                UserPushToken.user_id == user_id,
            )
        )
        await self.session.commit()

    async def list_by_user_id(self, user_id: int) -> List[UserPushToken]:
        result = await self.session.execute(select(UserPushToken).where(UserPushToken.user_id == user_id))
        return list(result.scalars().all())

    async def delete_by_tokens(self, push_tokens: List[str]) -> None:
        """Delete em lote por push_token -- usado pelo handler de envio
        (core/jobs/handlers.py::_send_push) quando o Expo confirma
        DeviceNotRegistered. Um só round-trip mesmo quando vários tokens
        morreram na mesma leva de envio, em vez de um DELETE por token."""
        if not push_tokens:
            return
        await self.session.execute(delete(UserPushToken).where(UserPushToken.push_token.in_(push_tokens)))
        await self.session.commit()
