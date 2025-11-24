from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from hack.core.services.appeal_routing import AppealRoutingService
from hack.core.services.uow_ctl import UoWCtl


class ProviderServices(Provider):
    get_appeal_routing_service = provide(
        AppealRoutingService,
        scope=Scope.REQUEST,
    )

    @provide(scope=Scope.REQUEST)
    async def get_uow_ctl(
            self,
            orm_session: AsyncSession,
    ) -> UoWCtl:
        return orm_session
