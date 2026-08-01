from typing import Optional, Protocol

from app.infrastructure.database.models import User


class UserRepository(Protocol):
    """Contrato que qualquer implementação de repositório de usuário deve seguir.

    Usar um Protocol aqui permite que a camada de aplicação dependa apenas
    dessa interface, sem saber se por trás existe SQLAlchemy, um banco em
    memória (útil em testes) ou qualquer outra tecnologia de persistência.
    """

    async def get_by_id(self, user_id: int) -> Optional[User]: ...

    async def get_by_email(self, email: str) -> Optional[User]: ...

    async def get_by_username(self, username: str) -> Optional[User]: ...

    async def create(self, email: str, password_hash: str, username: str) -> User: ...

    async def try_deduct_credits(self, user_id: int, amount: int) -> bool:
        """Desconta créditos de forma ATÔMICA (UPDATE condicional no
        banco -- credits_remaining = credits_remaining - amount WHERE
        credits_remaining >= amount -- não um read-modify-write em dois
        passos). Evita a mesma classe de corrida corrigida em
        CompleteMissionUseCase: duas requisições concorrentes lendo o
        mesmo saldo antes de qualquer uma gravar poderiam gastar mais
        crédito do que o usuário realmente tem.

        Devolve True se descontou (tinha saldo suficiente), False se não
        tinha -- quem chama deve tratar False como 402 Payment Required,
        não como erro interno."""
        ...

    async def refund_credits(self, user_id: int, amount: int) -> None:
        """Devolve créditos -- usado quando uma ação que já foi cobrada
        (ex: criar roadmap) termina rejeitada ou falha em todas as
        tentativas, pra não cobrar por algo que não aconteceu de verdade."""
        ...