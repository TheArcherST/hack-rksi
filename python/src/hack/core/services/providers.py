from argon2 import PasswordHasher
from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import AsyncBroker

from hack.core.services.access import AccessService
from hack.core.services.email_factory import EmailFactory
from hack.core.services.notification import NotificationService
from hack.core.services.uow_ctl import UoWCtl
from hack.core.providers import ConfigTemplates


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

    @provide(scope=Scope.APP)
    def get_email_factory(
            self,
            config_templates: ConfigTemplates,
    ) -> EmailFactory:
        return EmailFactory(config_templates=config_templates)

    @provide(scope=Scope.REQUEST)
    def get_notification_service(
            self,
            orm_session: AsyncSession,
            broker: AsyncBroker,
            email_factory: EmailFactory,
    ) -> NotificationService:
        return NotificationService(
            session=orm_session,
            broker=broker,
            email_factory=email_factory,
        )
