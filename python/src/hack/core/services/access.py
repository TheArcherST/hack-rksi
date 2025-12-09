import secrets
import uuid
from hmac import compare_digest
from uuid import UUID

from argon2 import PasswordHasher
from argon2 import exceptions as argon2_exceptions
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hack.core.errors.access import ErrorUnauthorized, ErrorVerification, \
    ErrorEmailAlreadyExists
from hack.core.models import LoginSession, User, IssuedRegistration


class AccessService:
    def __init__(
            self,
            orm_session: AsyncSession,
            ph: PasswordHasher,
    ):
        self.orm_session = orm_session
        self.ph = ph

    async def issue_registration(
            self,
            email: EmailStr,
            password: str,
            full_name: str
    ) -> IssuedRegistration:
        stmt = (select(User.id)
                .where(User.email == email))
        existing_user_id = await self.orm_session.scalar(stmt)
        if existing_user_id is not None:
            raise ErrorEmailAlreadyExists

        password_hash = self.ph.hash(password)
        verification_code = secrets.randbelow(900000) + 100000
        token = uuid.uuid4()
        issued_registration = IssuedRegistration(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            verification_code=verification_code,
            token=token,
        )
        self.orm_session.add(issued_registration)

        return issued_registration

    async def verify_registration(
            self,
            issued_registration_token: UUID,
            code: int,
    ) -> User:
        stmt = (select(IssuedRegistration)
                .where(IssuedRegistration.token == issued_registration_token)
                .order_by(IssuedRegistration.created_at.desc()))
        issued_registration = await self.orm_session.scalar(stmt)
        if issued_registration is None:
            raise ErrorVerification
        if not compare_digest(
                str(code),
                str(issued_registration.verification_code)
        ):
            raise ErrorVerification

        user = User(
            username=issued_registration.email,
            email=issued_registration.email,
            password_hash=issued_registration.password_hash,
            full_name=issued_registration.full_name,
        )
        self.orm_session.add(user)
        await self.orm_session.flush()

        return user

    async def login(
            self,
            email: str,
            password: str,
            user_agent: str | None,
    ) -> LoginSession:
        """
        :raise ErrorUnauthorized:
        """

        # note: timing-attack protected, but registration may expose
        #  if user with the username registered or not nevertheless, if it's
        #  not protected from unauthorized access.

        user = await self._identify_user(email)
        if user is None:
            await self._dummy_authentication()
            raise ErrorUnauthorized
        await self._authenticate_user(user, password)

        login_session = LoginSession(
            user_agent=user_agent,
            token=secrets.token_hex(nbytes=32),
            user_id=user.id,
        )
        self.orm_session.add(login_session)
        await self.orm_session.flush()

        return login_session

    async def lookup_login_session(
            self,
            login_session_uid: UUID,
            login_session_token: str,
    ) -> LoginSession:
        login_session = await self.orm_session.get(
            LoginSession, login_session_uid)

        if login_session is None:
            raise ErrorUnauthorized

        if not secrets.compare_digest(
                login_session.token,
                login_session_token,
        ):
            raise ErrorUnauthorized

        return login_session

    async def _identify_user(
            self,
            email: str,
    ) -> User | None:
        stmt = (select(User)
                .where(User.email == email))
        user = await self.orm_session.scalar(stmt)
        return user

    async def _dummy_authentication(
            self,
    ):
        dummy_hash = ("$argon2id$v=19$m=65536,t=3,p=4$1/kKopFhFTmJP0aLfW"
                      "15XQ$fwP4HIJ1Dwtk7Fb5XzW8HDenJ7WroA6fiz0FAynO1cA")
        dummy_password = "dummy password horse battery"
        self.ph.verify(dummy_hash, dummy_password)
        await self._dummy_rehash()

    async def _dummy_rehash(self):
        self.ph.hash("password horse battery dummy")

    async def _authenticate_user(
            self,
            user: User,
            password: str,
    ) -> None:
        try:
            self.ph.verify(user.password_hash, password)
        except argon2_exceptions.VerifyMismatchError as e:
            await self._dummy_rehash()
            raise ErrorUnauthorized from e

        if self.ph.check_needs_rehash(user.password_hash):
            user.password_hash = self.ph.hash(password)
        else:
            await self._dummy_rehash()

        return None
