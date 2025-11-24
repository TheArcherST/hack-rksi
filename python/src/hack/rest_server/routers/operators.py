from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hack.core.models import Operator
from hack.core.services.uow_ctl import UoWCtl
from hack.rest_server.schemas.operators import (
    OperatorDTO,
    CreateOperatorDTO,
    UpdateOperatorDTO,
)


router = APIRouter(
    prefix="/operators",
)


@router.post(
    "",
    response_model=OperatorDTO,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_operator(
    session: FromDishka[AsyncSession],
    uow_ctl: FromDishka[UoWCtl],
    payload: CreateOperatorDTO,
) -> Operator:
    operator = Operator(
        status=payload.status,
        active_appeals_limit=payload.active_appeals_limit,
    )
    session.add(operator)
    await session.flush()
    await uow_ctl.commit()
    return operator


@router.put(
    "/{operator_id}",
    response_model=OperatorDTO,
)
@inject
async def update_operator(
    session: FromDishka[AsyncSession],
    uow_ctl: FromDishka[UoWCtl],
    operator_id: int,
    payload: UpdateOperatorDTO,
) -> Operator:
    stmt = (select(Operator)
            .where(Operator.id == operator_id))
    operator = await session.scalar(stmt)

    if operator is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator not found",
        )

    operator.status = payload.status
    operator.active_appeals_limit = payload.active_appeals_limit

    await session.flush()
    await uow_ctl.commit()
    return operator


@router.delete(
    "/{operator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
async def delete_operator(
    session: FromDishka[AsyncSession],
    uow_ctl: FromDishka[UoWCtl],
    operator_id: int,
) -> None:
    stmt = (select(Operator)
            .where(Operator.id == operator_id))
    operator = await session.scalar(stmt)

    if operator is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator not found",
        )

    await session.delete(operator)
    await session.flush()
    await uow_ctl.commit()
    return None


@router.get(
    "",
    response_model=list[OperatorDTO],
)
@inject
async def list_operators(
    session: FromDishka[AsyncSession],
) -> list[Operator]:
    stmt = (select(Operator)
            .order_by(Operator.id))
    operators = await session.scalars(stmt)
    return list(operators)


@router.get(
    "/{operator_id}",
    response_model=OperatorDTO,
)
@inject
async def get_operator(
    session: FromDishka[AsyncSession],
    operator_id: int,
) -> Operator:
    stmt = (select(Operator)
            .where(Operator.id == operator_id))
    operator = await session.scalar(stmt)

    if operator is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator not found",
        )

    return operator
