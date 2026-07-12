from app.core.security import hash_password
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.database.models import User


class EmailAlreadyRegisteredError(Exception):
    """Levantado quando já existe um usuário cadastrado com esse e-mail."""


class RegisterUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, email: str, password: str) -> User:
        existing_user = await self.user_repository.get_by_email(email)
        if existing_user is not None:
            raise EmailAlreadyRegisteredError(f"O e-mail {email} já está cadastrado.")

        password_hash = hash_password(password)
        return await self.user_repository.create(email=email, password_hash=password_hash)
