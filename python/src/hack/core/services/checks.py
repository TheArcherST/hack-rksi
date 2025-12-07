from __future__ import annotations
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hack.core.models import Check, CheckStatusEnum, CheckTypeEnum


class ErrorCheckNotFound(Exception):
    pass


class ChecksService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_check(
            self,
            *,
            check_type: CheckTypeEnum,
            target: str,
            parameters: dict[str, Any] | None = None,
    ) -> Check:
        check = Check(
            type=check_type,
            target=target,
            parameters=parameters,
        )
        self._session.add(check)
        await self._session.flush()
        return check

    async def list_checks(self) -> list[Check]:
        result = await self._session.scalars(
            select(Check).order_by(Check.id)
        )
        return list(result)

    async def get_check(self, check_id: int) -> Check:
        check = await self._session.get(Check, check_id)
        if check is None:
            raise ErrorCheckNotFound
        return check

    async def update_check_status(
            self,
            *,
            check_id: int,
            status: CheckStatusEnum | None = None,
            started_at: datetime | None = None,
            finished_at: datetime | None = None,
            message: str | None = None,
            result: dict[str, Any] | None = None,
    ) -> Check:
        check = await self.get_check(check_id)

        if status is not None:
            check.status = status
        if started_at is not None:
            check.started_at = started_at
        if finished_at is not None:
            check.finished_at = finished_at
        if message is not None:
            check.message = message
        if result is not None:
            check.result = result

        await self._session.flush()
        return check
