from typing import Optional

from app.core.security import verify_password
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.database.models import User


class UserNotFoundError(Exception):
    """Levantado quando o usuário do token não existe mais no banco
    (situação improvável -- o próprio get_current_user já buscou o
    usuário momentos antes -- mas defensivo contra corrida com outra
    exclusão concorrente)."""


class IncorrectPasswordError(Exception):
    """Levantado quando a senha informada pra confirmar a exclusão não
    bate com a da conta."""


class PasswordConfirmationRequiredError(Exception):
    """Levantado quando a conta TEM senha (não é só-OAuth) e nenhuma
    senha foi informada pra confirmar -- ver DeleteAccountUseCase."""


class DeleteAccountUseCase:
    """Apaga a conta autenticada e tudo que pertence a ela (ver
    UserRepository.delete_account pra escopo completo). Irreversível --
    não existe undo, não existe "restaurar conta apagada".

    Exige reautenticação por senha antes de apagar, na mesma linha de
    qualquer "excluir conta" de produto real (Google, GitHub, etc.):
    protege contra o cenário de um token JWT vazado/sequestrado ser
    suficiente sozinho pra destruir a conta -- alguém com acesso à sessão
    mas sem a senha não consegue completar a exclusão.

    Exceção: contas criadas só via login social (Google/Facebook) não têm
    senha (User.password_hash é None nesse caso, ver login_with_oauth.py)
    -- não tem o que confirmar, então essas apagam só com o JWT válido
    mesmo, sem pedir senha (pedir uma senha que nunca existiu não
    protegeria nada, só frustraria a pessoa)."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: int, password: Optional[str]) -> None:
        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError()

        self._verify_identity(user, password)

        await self.user_repository.delete_account(user_id)

    def _verify_identity(self, user: User, password: Optional[str]) -> None:
        if user.password_hash is None:
            return

        if not password:
            raise PasswordConfirmationRequiredError()

        if not verify_password(password, user.password_hash):
            raise IncorrectPasswordError()
