from sqlalchemy.ext.asyncio import AsyncSession

from hack.core.models import Appeal, Operator
from hack.core.models.appeal import AppealStatusEnum


class AppealService:
    def __init__(
            self,
            session: AsyncSession,
    ):
        self._session = session

    async def assign_operator(
            self,
            appeal: Appeal,
            operator: Operator,
    ) -> None:
        appeal.assigned_operator_id = operator.id
        if appeal.status is AppealStatusEnum.ACTIVE:
            operator.active_appeals += 1
        await self._session.flush()

    async def change_status(
            self,
            appeal: Appeal,
            new_status: AppealStatusEnum,
    ) -> None:
        if (appeal.status is not AppealStatusEnum.ACTIVE
            and new_status is AppealStatusEnum.ACTIVE
            and appeal.assigned_operator_id is not None):
            operator = await appeal.awaitable_attrs.assigned_operator
            operator.active_appeals -= 1
            await self._session.flush()
