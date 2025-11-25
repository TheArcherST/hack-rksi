from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from hack.core.models import Lead, Appeal
from hack.rest_server.schemas.inspect import (
    LeadWithAppealsDTO,
    LeadAppealDTO,
    AppealDistributionItemDTO,
)


router = APIRouter(
    prefix="/inspect",
)


@router.get(
    "/leads",
    response_model=list[LeadWithAppealsDTO],
)
@inject
async def list_leads_with_appeals(
    session: FromDishka[AsyncSession],
) -> list[LeadWithAppealsDTO]:
    stmt_leads = (
        select(Lead)
        .order_by(Lead.id)
        .options(joinedload(Lead.appeals))
    )
    leads_result = await session.scalars(stmt_leads)
    leads = list(leads_result.unique())

    if not leads:
        return []

    items: list[LeadWithAppealsDTO] = []

    for lead in leads:
        appeals_dto = [
            LeadAppealDTO(
                id=a.id,
                status=a.status,
                lead_source_id=a.lead_source_id,
                assigned_operator_id=a.assigned_operator_id,
                created_at=a.created_at,
            )
            for a in lead.appeals
        ]

        items.append(
            LeadWithAppealsDTO(
                id=lead.id,
                created_at=lead.created_at,
                appeals=appeals_dto,
            )
        )

    return items


@router.get(
    "/appeals-distribution",
    response_model=list[AppealDistributionItemDTO],
)
@inject
async def get_appeals_distribution(
    session: FromDishka[AsyncSession],
) -> list[AppealDistributionItemDTO]:
    stmt = (
        select(
            Appeal.lead_source_id,
            Appeal.assigned_operator_id,
            func.count(Appeal.id).label("appeals_count"),
        )
        .group_by(
            Appeal.lead_source_id,
            Appeal.assigned_operator_id,
        )
        .order_by(
            Appeal.lead_source_id,
            Appeal.assigned_operator_id,
        )
    )

    result = await session.execute(stmt)
    rows = result.all()

    items: list[AppealDistributionItemDTO] = []
    for lead_source_id, assigned_operator_id, appeals_count in rows:
        items.append(
            AppealDistributionItemDTO(
                lead_source_id=lead_source_id,
                assigned_operator_id=assigned_operator_id,
                appeals_count=appeals_count,
            )
        )

    return items
