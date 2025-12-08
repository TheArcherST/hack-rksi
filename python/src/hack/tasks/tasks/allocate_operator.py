import asyncio
from typing import Annotated

from dishka import FromDishka
from dishka.integrations.taskiq import inject
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import Context, TaskiqDepends, NoResultError

from hack.core.errors.appeal_routing import NoAvailableOperatorError
from hack.core.models import Appeal
from hack.core.services.appeal import AppealService
from hack.core.services.appeal_routing import AppealRoutingService
from hack.core.services.uow_ctl import UoWCtl
from hack.tasks.brokers.default import default_broker


@default_broker.task()
@inject(patch_module=True)
async def allocate_operator(
        context: Annotated[Context, TaskiqDepends()],
        routing_service: FromDishka[AppealRoutingService],
        appeal_service: FromDishka[AppealService],
        session: FromDishka[AsyncSession],
        uow_ctl: FromDishka[UoWCtl],
        appeal_id: int,
) -> None:
    appeal = await session.get(Appeal, appeal_id)

    if appeal is None:
        label = "X-Application-reread-count"
        retry_count = int(context.message.labels.get(label, 0))
        if retry_count >= 3:
            raise RuntimeError(
                f"Re-read retries exceeded: cannot"
                f" find appeal with {appeal_id=}"
            )
        retry_count += 1
        await asyncio.sleep(retry_count)
        context.message.labels[label] = str(retry_count)
        await context.broker.kick(context.broker.formatter.dumps(
            context.message))
        raise NoResultError

    try:
        operator = await routing_service.allocate_operator(appeal)
    except NoAvailableOperatorError:
        await session.rollback()
        await asyncio.sleep(3)
        await context.requeue()
    else:
        await appeal_service.assign_operator(
            appeal=appeal,
            operator=operator,
        )
        await uow_ctl.commit()
