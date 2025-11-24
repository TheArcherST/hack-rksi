from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hack.core.models import LeadSource
from hack.core.services.uow_ctl import UoWCtl
from hack.rest_server.schemas.lead_sources import (
    LeadSourceDTO,
    CreateLeadSourceDTO,
    UpdateLeadSourceDTO,
)


router = APIRouter(
    prefix="/lead-sources",
)


@router.post(
    "",
    response_model=LeadSourceDTO,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_lead_source(
    session: FromDishka[AsyncSession],
    uow_ctl: FromDishka[UoWCtl],
    payload: CreateLeadSourceDTO,
) -> LeadSource:
    lead_source = LeadSource(
        type=payload.type,
    )
    session.add(lead_source)
    await session.flush()
    await uow_ctl.commit()
    return lead_source


@router.put(
    "/{lead_source_id}",
    response_model=LeadSourceDTO,
)
@inject
async def update_lead_source(
    session: FromDishka[AsyncSession],
    uow_ctl: FromDishka[UoWCtl],
    lead_source_id: int,
    payload: UpdateLeadSourceDTO,
) -> LeadSource:
    stmt = (select(LeadSource)
            .where(LeadSource.id == lead_source_id))
    lead_source = await session.scalar(stmt)

    if lead_source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead source not found",
        )

    # update code here
    await session.flush()
    await uow_ctl.commit()

    return lead_source


@router.delete(
    "/{lead_source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
async def delete_lead_source(
    session: FromDishka[AsyncSession],
    uow_ctl: FromDishka[UoWCtl],
    lead_source_id: int,
) -> None:
    stmt = (select(LeadSource)
            .where(LeadSource.id == lead_source_id))
    lead_source = await session.scalar(stmt)

    if lead_source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead source not found",
        )

    await session.delete(lead_source)
    await session.flush()
    await uow_ctl.commit()
    return None


@router.get(
    "",
    response_model=list[LeadSourceDTO],
)
@inject
async def list_lead_sources(
    session: FromDishka[AsyncSession],
) -> list[LeadSource]:
    stmt = (select(LeadSource)
            .order_by(LeadSource.id))
    lead_sources = await session.scalars(stmt)
    return list(lead_sources)


@router.get(
    "/{lead_source_id}",
    response_model=LeadSourceDTO,
)
@inject
async def get_lead_source(
    session: FromDishka[AsyncSession],
    lead_source_id: int,
) -> LeadSource:
    stmt = (select(LeadSource)
            .where(LeadSource.id == lead_source_id))
    lead_source = await session.scalar(stmt)

    if lead_source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead source not found",
        )

    return lead_source
