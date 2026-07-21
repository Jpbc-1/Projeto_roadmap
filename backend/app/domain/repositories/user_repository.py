from typing import Optional, Protocol

from app.infrastructure.database.models import User


class UserRepository(Protocol):
    """Contrato que qualquer implementação de repositório de usuário deve seguir.

    Usar um Protocol aqui permite que a camada de aplicação dependa apenas
    dessa interface, sem saber se por trás existe SQLAlchemy, um banco em
    memória (útil em testes) ou qualquer outra tecnologia de persistência.
    """

    async def get_by_email(self, email: str) -> Optional[User]: ...

    async def get_by_username(self, username: str) -> Optional[User]: ...

    async def create(self, email: str, password_hash: str, username: str) -> User: ...