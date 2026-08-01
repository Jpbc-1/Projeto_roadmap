from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import User


class SQLAlchemyUserRepository:
    """Implementação real do UserRepository, usando SQLAlchemy + Postgres."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> Optional[User]:
        return await self.session.get(User, user_id)

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

    async def try_deduct_credits(self, user_id: int, amount: int) -> bool:
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id, User.credits_remaining >= amount)
            .values(credits_remaining=User.credits_remaining - amount)
        )
        await self.session.commit()
        return result.rowcount > 0

    async def refund_credits(self, user_id: int, amount: int) -> None:
        await self.session.execute(
            update(User).where(User.id == user_id).values(credits_remaining=User.credits_remaining + amount)
        )
        await self.session.commit()