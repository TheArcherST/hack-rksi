import logging
from typing import Annotated

from dishka.integrations.taskiq import inject
from taskiq import Context, TaskiqDepends

from hack.tasks.brokers.default import default_broker

logger = logging.getLogger(__name__)


@default_broker.task()
@inject(patch_module=True)
async def notify_user(
        context: Annotated[Context, TaskiqDepends()],
        user_id: int,
        title: str,
        content: str,
) -> None:
    logger.info(
        "notify_user task called; user_id=%s title=%s content=%s "
        "task_id=%s",
        user_id,
        title,
        content,
        context.message.task_id,
    )
