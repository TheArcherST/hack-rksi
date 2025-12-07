from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hack.core.models.operator import LeadSourceOperator
from hack.core.services.uow_ctl import UoWCtl
from hack.rest_server.schemas.lead_source_operators import (
    LeadSourceOperatorDTO,
    CreateLeadSourceOperatorDTO,
    UpdateLeadSourceOperatorDTO,
)


router = APIRouter(
    prefix="/lead-sources/{lead_source_id}/operators",
)


@router.post(
    "",
    response_model=LeadSourceOperatorDTO,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_lead_source_operator(
    session: FromDishka[AsyncSession],
    uow_ctl: FromDishka[UoWCtl],
    lead_source_id: int,
    payload: CreateLeadSourceOperatorDTO,
) -> LeadSourceOperator:
    lead_source_operator = LeadSourceOperator(
        lead_source_id=lead_source_id,
        operator_id=payload.operator_id,
        routing_factor=payload.routing_factor,
    )
    session.add(lead_source_operator)
    await session.flush()
    await uow_ctl.commit()
    return lead_source_operator


@router.get(
    "",
    response_model=list[LeadSourceOperatorDTO],
)
@inject
async def list_lead_source_operators(
    session: FromDishka[AsyncSession],
    lead_source_id: int,
) -> list[LeadSourceOperator]:
    stmt = (
        select(LeadSourceOperator)
        .where(LeadSourceOperator.lead_source_id == lead_source_id)
        .order_by(LeadSourceOperator.id)
    )
    lead_source_operators = await session.scalars(stmt)
    return list(lead_source_operators)


@router.get(
    "/{lead_source_operator_id}",
    response_model=LeadSourceOperatorDTO,
)
@inject
async def get_lead_source_operator(
    session: FromDishka[AsyncSession],
    lead_source_id: int,
    lead_source_operator_id: int,
) -> LeadSourceOperator:
    stmt = (
        select(LeadSourceOperator)
        .where(
            LeadSourceOperator.id == lead_source_operator_id,
            LeadSourceOperator.lead_source_id == lead_source_id,
        )
    )
    lead_source_operator = await session.scalar(stmt)

    if lead_source_operator is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead source operator not found",
        )

    return lead_source_operator


@router.put(
    "/{lead_source_operator_id}",
    response_model=LeadSourceOperatorDTO,
)
@inject
async def update_lead_source_operator(
    session: FromDishka[AsyncSession],
    uow_ctl: FromDishka[UoWCtl],
    lead_source_id: int,
    lead_source_operator_id: int,
    payload: UpdateLeadSourceOperatorDTO,
) -> LeadSourceOperator:
    stmt = (
        select(LeadSourceOperator)
        .where(
            LeadSourceOperator.id == lead_source_operator_id,
            LeadSourceOperator.lead_source_id == lead_source_id,
        )
    )
    lead_source_operator = await session.scalar(stmt)

    if lead_source_operator is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead source operator not found",
        )

    lead_source_operator.routing_factor = payload.routing_factor
    await session.flush()
    await uow_ctl.commit()

    return lead_source_operator


@router.delete(
    "/{lead_source_operator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
async def delete_lead_source_operator(
    session: FromDishka[AsyncSession],
    uow_ctl: FromDishka[UoWCtl],
    lead_source_id: int,
    lead_source_operator_id: int,
) -> None:
    stmt = (
        select(LeadSourceOperator)
        .where(
            LeadSourceOperator.id == lead_source_operator_id,
            LeadSourceOperator.lead_source_id == lead_source_id,
        )
    )
    lead_source_operator = await session.scalar(stmt)

    if lead_source_operator is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead source operator not found",
        )

    await session.delete(lead_source_operator)
    await session.flush()
    await uow_ctl.commit()
    return None
