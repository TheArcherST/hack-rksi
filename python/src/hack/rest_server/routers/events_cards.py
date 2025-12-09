from datetime import datetime, timezone

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from hack.core.models import Event, EventParticipant
from hack.core.models.event import EventStatusEnum
from hack.rest_server.models import AuthorizedUser
from hack.rest_server.schemas.events import EventCardDTO, \
    ParticipationStatusEnum


router = APIRouter(
    prefix="/events/cards",
)


async def _fetch_participants_count(
        session: AsyncSession,
        event_ids: list[int],
) -> dict[int, int]:
    if not event_ids:
        return {}
    stmt = (
        select(
            EventParticipant.event_id,
            func.count(EventParticipant.id),
        )
        .where(EventParticipant.event_id.in_(event_ids))
        .where(
            EventParticipant.status
            == EventParticipant.ParticipationStatusEnum.PARTICIPATING
        )
        .group_by(EventParticipant.event_id)
    )
    result = await session.execute(stmt)
    return {event_id: count for event_id, count in result.all()}


async def _fetch_user_participation(
        session: AsyncSession,
        event_ids: list[int],
        user_id: int,
) -> dict[int, EventParticipant.ParticipationStatusEnum]:
    if not event_ids:
        return {}
    stmt = (
        select(EventParticipant.event_id, EventParticipant.status)
        .where(EventParticipant.event_id.in_(event_ids))
        .where(EventParticipant.user_id == user_id)
    )
    result = await session.execute(stmt)
    return {event_id: status for event_id, status in result.all()}


@router.get(
    "",
    response_model=list[EventCardDTO],
)
@inject
async def list_event_cards(
    session: FromDishka[AsyncSession],
    authorized_user: FromDishka[AuthorizedUser],
    status_filter: EventStatusEnum | None = Query(
        default=None,
        alias="status",
    ),
) -> list[EventCardDTO]:
    now = datetime.now(tz=timezone.utc)
    stmt = (
        select(Event)
        .where(Event.rejected_at.is_(None))
        .order_by(Event.starts_at, Event.id)
    )

    if status_filter in (None, EventStatusEnum.ACTIVE):
        stmt = stmt.where(Event.ends_at > now)
    elif status_filter is EventStatusEnum.REJECTED:
        return []
    elif status_filter is EventStatusEnum.PAST:
        stmt = stmt.where(Event.ends_at <= now)

    events = await session.scalars(stmt)
    events = list(events.unique())

    event_ids = [e.id for e in events]
    participants_count = await _fetch_participants_count(session, event_ids)
    user_participation = await _fetch_user_participation(
        session,
        event_ids,
        authorized_user.id,
    )

    cards: list[EventCardDTO] = []
    for event in events:
        participation_status = user_participation.get(event.id)
        if participation_status is None:
            participation_status_dto = ParticipationStatusEnum.NONE
        elif participation_status == EventParticipant.ParticipationStatusEnum.PARTICIPATING:
            participation_status_dto = ParticipationStatusEnum.PARTICIPATING
        else:
            participation_status_dto = ParticipationStatusEnum.REJECTED

        cards.append(
            EventCardDTO(
                id=event.id,
                name=event.name,
                short_description=event.short_description,
                description=event.description,
                starts_at=event.starts_at,
                ends_at=event.ends_at,
                image_url=event.image_url,
                participants_count=participants_count.get(event.id, 0),
                max_participants_count=event.max_participants_count,
                payment_info=event.payment_info,
                status=event.status,
                participation_status=participation_status_dto,
            )
        )

    return cards
