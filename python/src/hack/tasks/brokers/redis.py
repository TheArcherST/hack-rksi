from dishka import (
    make_container,
    make_async_container,
    Provider,
    Scope,
    provide,
)
from dishka.integrations import taskiq as dishka_taskiq_integration
from dishka.integrations.taskiq import (
    setup_dishka,
    TaskiqProvider,
)
from taskiq import SimpleRetryMiddleware, TaskiqMessage, BrokerMessage
from taskiq.formatters.proxy_formatter import ProxyFormatter
from taskiq_redis import ListQueueBroker

from hack.core.providers import (
    ProviderDatabase,
    ProviderConfig,
    ConfigRedis,
)
from hack.tasks.providers import ProviderBroker


class DishkaFormatter(ProxyFormatter):
    def dumps(self, message: TaskiqMessage) -> BrokerMessage:
        labels = message.labels.copy()
        del labels[dishka_taskiq_integration.CONTAINER_NAME]
        message = message.model_copy(update={"labels": labels})
        return super().dumps(message)


def make_worker_broker():
    from hack.core.services.providers import ProviderServices
    from hack.rest_server.models import AuthorizedUser

    class NoAuthorizedUser(Provider):
        @provide(scope=Scope.APP)
        async def get_authorized_user(self) -> AuthorizedUser:
            return None

    # configure config DI
    config_providers = (
        ProviderConfig(),
    )
    config_container = make_container(*config_providers)
    providers = (
        ProviderConfig(),
        ProviderDatabase(),
        ProviderBroker(),
        ProviderServices(),
        NoAuthorizedUser(),
        TaskiqProvider(),
    )
    container = make_async_container(*providers)

    # configure broker for tasks
    config_redis = config_container.get(ConfigRedis)
    broker = (
        ListQueueBroker(f"redis"
                        f"://{config_redis.host}"
                        f":{config_redis.port}"
                        f"/{config_redis.db}")
        .with_middlewares(SimpleRetryMiddleware(default_retry_count=3))
    )
    broker = (
        broker
        .with_formatter(DishkaFormatter(broker))
    )

    # setup DI for this broker
    setup_dishka(container=container, broker=broker)

    return broker
