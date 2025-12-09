import secrets

from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hack.core.models import User
from hack.core.errors.verification import ErrorVerification


class VerificationService:
    def __init__(
            self,
            orm_session: AsyncSession,
    ):
        self.orm_session = orm_session

    async def issue_code(
            self,
            user: User,
    ) -> int:
        code = secrets.randbelow(900000) + 100000
        user.verification_code = code
        user.is_verified = False
        await self.orm_session.flush()
        return code

    async def verify_by_code(
            self,
            email: EmailStr,
            code: int,
    ) -> User:
        stmt = (select(User)
                .where(User.email == email))
        user = await self.orm_session.scalar(stmt)

        if user is None:
            raise ErrorVerification

        if user.is_verified:
            return user

        if user.verification_code != code:
            raise ErrorVerification

        user.is_verified = True
        user.verification_code = None
        await self.orm_session.flush()

        return user
