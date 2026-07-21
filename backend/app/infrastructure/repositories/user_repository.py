from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import User


class SQLAlchemyUserRepository:
    """Implementação real do UserRepository, usando SQLAlchemy + Postgres."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def create(self, email: str, password_hash: str, username: str) -> User:
        user = User(email=email, password_hash=password_hash, username=username)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user