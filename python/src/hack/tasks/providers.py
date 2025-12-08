from dishka import Provider, provide, Scope
from taskiq import SimpleRetryMiddleware, AsyncBroker
from taskiq_redis import ListQueueBroker

from hack.core.providers import ConfigRedis


class ProviderBroker(Provider):
    @provide(scope=Scope.APP)
    async def get_broker(
            self,
            config_redis: ConfigRedis,
    ) -> AsyncBroker:
        broker = (
            ListQueueBroker(f"redis"
                            f"://{config_redis.host}"
                            f":{config_redis.port}"
                            f"/{config_redis.db}")
            .with_middlewares(SimpleRetryMiddleware(default_retry_count=3))
        )
        return broker
