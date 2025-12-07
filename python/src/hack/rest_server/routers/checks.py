from datetime import datetime, timezone

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException

from hack.core.models import CheckStatusEnum
from hack.core.services.checks import ChecksService, ErrorCheckNotFound
from hack.core.services.uow_ctl import UoWCtl
from hack.rest_server.schemas.checks import (
    CheckDTO,
    CreateCheckDTO,
    UpdateCheckDTO,
)


router = APIRouter(
    prefix="/checks",
)


@router.post(
    "",
    status_code=201,
    response_model=CheckDTO,
)
@inject
async def create_check(
        checks_service: FromDishka[ChecksService],
        uow_ctl: FromDishka[UoWCtl],
        payload: CreateCheckDTO,
) -> CheckDTO:
    check = await checks_service.create_check(
        check_type=payload.type,
        target=payload.target,
        parameters=payload.parameters,
    )
    await uow_ctl.commit()
    return check


@router.get(
    "",
    response_model=list[CheckDTO],
)
@inject
async def list_checks(
        checks_service: FromDishka[ChecksService],
) -> list[CheckDTO]:
    return await checks_service.list_checks()


@router.get(
    "/{check_id}",
    response_model=CheckDTO,
)
@inject
async def get_check(
        checks_service: FromDishka[ChecksService],
        check_id: int,
) -> CheckDTO:
    try:
        return await checks_service.get_check(check_id)
    except ErrorCheckNotFound as e:
        raise HTTPException(
            status_code=404,
            detail="Check not found",
        ) from e


@router.patch(
    "/{check_id}",
    response_model=CheckDTO,
)
@inject
async def update_check(
        checks_service: FromDishka[ChecksService],
        uow_ctl: FromDishka[UoWCtl],
        check_id: int,
        payload: UpdateCheckDTO,
) -> CheckDTO:
    try:
        check = await checks_service.update_check_status(
            check_id=check_id,
            status=payload.status,
            started_at=payload.started_at,
            finished_at=payload.finished_at,
            message=payload.message,
            result=payload.result,
        )
    except ErrorCheckNotFound as e:
        raise HTTPException(
            status_code=404,
            detail="Check not found",
        ) from e

    if payload.status == CheckStatusEnum.RUNNING and check.started_at is None:
        check.started_at = payload.started_at or datetime.now(tz=timezone.utc)
    if payload.status == CheckStatusEnum.SUCCESS and check.finished_at is None:
        check.finished_at = payload.finished_at or datetime.now(
            tz=timezone.utc,
        )

    await uow_ctl.commit()
    return check
