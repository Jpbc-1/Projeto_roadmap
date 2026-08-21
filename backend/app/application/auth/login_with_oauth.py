import re
from typing import Optional

from app.core.oauth.profile import OAuthProfile
from app.domain.repositories.oauth_account_repository import OAuthAccountRepository
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.database.models import User


class LoginWithOAuthUseCase:
    """
    Ordem sempre igual, qualquer provider:

    1. Já existe um OAuthAccount pra esse provider+provider_user_id? É
       login direto, devolve o User vinculado.
    2. Não existe OAuthAccount, mas já existe um User com esse e-mail
       (cadastro normal por senha, ou vínculo de OUTRO provider)? Vincula
       essa OAuthAccount nova ao User existente -- nunca cria duplicata.
    3. Não existe nada? Cria User novo (password_hash=None -- só entra
       por OAuth até decidir criar uma senha, se quiser) + a OAuthAccount.
    """

    def __init__(self, user_repository: UserRepository, oauth_account_repository: OAuthAccountRepository):
        self.user_repository = user_repository
        self.oauth_account_repository = oauth_account_repository

    async def execute(self, profile: OAuthProfile) -> User:
        existing_account = await self.oauth_account_repository.get_by_provider_id(
            profile.provider, profile.provider_user_id
        )
        if existing_account is not None:
            user = await self.user_repository.get_by_id(existing_account.user_id)
            if user is not None:
                return user

        user = await self.user_repository.get_by_email(profile.email)
        if user is None:
            username = await self._resolve_username(profile.email)
            user = await self.user_repository.create(
                email=profile.email, username=username, password_hash=None, email_verified=True
            )

        await self.oauth_account_repository.create(
            user_id=user.id,
            provider=profile.provider,
            provider_user_id=profile.provider_user_id,
            email=profile.email,
        )
        return user

    async def _resolve_username(self, email: str) -> str:
        base = re.sub(r"[^a-z0-9_]", "", email.split("@")[0].lower())[:20] or "user"
        candidate = base
        suffix = 2
        while await self.user_repository.get_by_username(candidate) is not None:
            candidate = f"{base}{suffix}"
            suffix += 1
        return candidate
