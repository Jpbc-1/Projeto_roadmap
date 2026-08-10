from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import OAuthAccount


class SQLAlchemyOAuthAccountRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_provider_id(self, provider: str, provider_user_id: str) -> Optional[OAuthAccount]:
        result = await self.session.execute(
            select(OAuthAccount).where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: int, provider: str, provider_user_id: str, email: str) -> OAuthAccount:
        account = OAuthAccount(user_id=user_id, provider=provider, provider_user_id=provider_user_id, email=email)
        self.session.add(account)
        await self.session.commit()
        await self.session.refresh(account)
        return account
