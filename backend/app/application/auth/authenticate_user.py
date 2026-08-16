from app.core.security import verify_password
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.database.models import User


class InvalidCredentialsError(Exception):
    """Levantado quando o e-mail não existe ou a senha não confere."""


class AuthenticateUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, email: str, password: str) -> User:
        user = await self.user_repository.get_by_email(email)
        if user is None or user.password_hash is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("E-mail ou senha inválidos.")
        return user
