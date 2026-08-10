from typing import Optional, Protocol

from app.infrastructure.database.models import OAuthAccount


class OAuthAccountRepository(Protocol):
    async def get_by_provider_id(self, provider: str, provider_user_id: str) -> Optional[OAuthAccount]: ...

    async def create(self, user_id: int, provider: str, provider_user_id: str, email: str) -> OAuthAccount: ...
