import re
from typing import Optional

from app.core.security import hash_password
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.database.models import User


class EmailAlreadyRegisteredError(Exception):
    """Levantado quando já existe um usuário cadastrado com esse e-mail."""


class UsernameAlreadyTakenError(Exception):
    """Levantado quando o usuário pediu um username específico que já existe."""


class RegisterUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, email: str, password: str, username: Optional[str] = None) -> User:
        existing_user = await self.user_repository.get_by_email(email)
        if existing_user is not None:
            raise EmailAlreadyRegisteredError(f"O e-mail {email} já está cadastrado.")

        final_username = await self._resolve_username(username, email)

        password_hash = hash_password(password)
        return await self.user_repository.create(
            email=email, password_hash=password_hash, username=final_username
        )

    async def _resolve_username(self, requested_username: Optional[str], email: str) -> str:
        if requested_username is not None:
            existing = await self.user_repository.get_by_username(requested_username)
            if existing is not None:
                raise UsernameAlreadyTakenError(f"O username '{requested_username}' já está em uso.")
            return requested_username

        base = self._slugify_email(email)
        candidate = base
        suffix = 2
        while await self.user_repository.get_by_username(candidate) is not None:
            candidate = f"{base}{suffix}"
            suffix += 1
        return candidate

    @staticmethod
    def _slugify_email(email: str) -> str:
        local_part = email.split("@")[0].lower()
        slug = re.sub(r"[^a-z0-9_]", "", local_part) or "user"
        return slug[:20]