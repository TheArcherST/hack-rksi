from argon2 import PasswordHasher
from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from hack.core.services.access import AccessService
from hack.core.services.uow_ctl import UoWCtl


class ProviderServices(Provider):
    get_access_service = provide(
        AccessService,
        scope=Scope.REQUEST,
    )

    @provide(scope=Scope.REQUEST)
    async def get_uow_ctl(
            self,
            orm_session: AsyncSession,
    ) -> UoWCtl:
        return orm_session

    @provide(scope=Scope.APP)
    def get_password_hasher(self) -> PasswordHasher:
        return PasswordHasher()
