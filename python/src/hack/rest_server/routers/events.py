from datetime import datetime, timezone

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from hack.core.models import (
    Event,
    EventCreatedNotification,
    EventParticipant,
    EventParticipationCancelledNotification,
    EventParticipationConfirmedNotification,
    EventUpdatedNotification,
    User,
)
from hack.core.models.user import UserRoleEnum
from hack.core.models.event import EventStatusEnum
from hack.core.services.uow_ctl import UoWCtl
from hack.core.services.notification import NotificationService
from hack.rest_server.models import AuthorizedAdministrator, AuthorizedUser
from hack.rest_server.schemas.events import (
    EventDTO,
    CreateEventDTO,
    UpdateEventDTO,
    UpdateMyParticipationDTO,
    ParticipationStatusEnum,
)

admin_panel_router = APIRouter(
    prefix="/events",
)
userspace_router = APIRouter(
    prefix="/events",
)


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _validate_event_dates(
    starts_at: datetime,
    ends_at: datetime,
    created_at: datetime,
) -> None:
    starts_at = _normalize_datetime(starts_at)
    ends_at = _normalize_datetime(ends_at)
    created_at = _normalize_datetime(created_at)

    if starts_at <= created_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="starts_at must be later than created_at",
        )
    if ends_at <= starts_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ends_at must be later than starts_at",
        )


def _validate_participants_limit(
    max_participants_count: int | None,
    participant_ids: list[int],
) -> None:
    if (
        max_participants_count is not None
        and len(participant_ids) > max_participants_count
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Max participants count exceeded",
        )


async def _ensure_users_exist(
    session: AsyncSession,
    participant_ids: list[int],
) -> None:
    if not participant_ids:
        return

    stmt = (
        select(User.id)
        .where(User.id.in_(participant_ids))
        .where(User.deleted_at.is_(None))
    )
    found_ids = await session.scalars(stmt)
    found_set = set(found_ids.all())
    missing = set(participant_ids) - found_set
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Some participants are missing or deleted",
        )


@admin_panel_router.post(
    "",
    response_model=EventDTO,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_event(
    session: FromDishka[AsyncSession],
    uow_ctl: FromDishka[UoWCtl],
    authorized_administrator: FromDishka[AuthorizedAdministrator],
    notification_service: FromDishka[NotificationService],
    payload: CreateEventDTO,
) -> Event:
    participant_ids = list(dict.fromkeys(payload.participants_ids))

    starts_at = _normalize_datetime(payload.starts_at)
    ends_at = _normalize_datetime(payload.ends_at)
    _validate_event_dates(
        starts_at=starts_at,
        ends_at=ends_at,
        created_at=datetime.now(tz=timezone.utc),
    )
    _validate_participants_limit(
        payload.max_participants_count,
        participant_ids,
    )
    await _ensure_users_exist(session, participant_ids)

    event = Event(
        name=payload.name,
        short_description=payload.short_description,
        description=payload.description,
        starts_at=starts_at,
        ends_at=ends_at,
        image_url=payload.image_url,
        payment_info=payload.payment_info,
        max_participants_count=payload.max_participants_count,
        location=payload.location,
        rejected_at=None,
    )
    session.add(event)
    event.participants = [
        EventParticipant(
            user_id=user_id,
            status=EventParticipant.ParticipationStatusEnum.PARTICIPATING,
        )
        for user_id in participant_ids
    ]
    await session.flush()
    if participant_ids:
        await notification_service.notify_about_event(
            EventCreatedNotification(
                event_name=event.name,
                starts_at=event.starts_at,
                location=event.location,
                event_id=event.id,
                participants_count=len(participant_ids),
            ),
            recipients_ids=participant_ids,
        )
    await uow_ctl.commit()
    return event


@admin_panel_router.get(
    "",
    response_model=list[EventDTO],
)
@inject
async def list_events(
    session: FromDishka[AsyncSession],
    authorized_administrator: FromDishka[AuthorizedAdministrator],
    status_filter: EventStatusEnum | None = Query(
        default=None,
        alias="status",
    ),
) -> list[Event]:
    now = datetime.now(tz=timezone.utc)
    stmt = (
        select(Event)
        .order_by(Event.id)
        .options(selectinload(Event.participants))
    )

    if status_filter == EventStatusEnum.REJECTED:
        stmt = stmt.where(Event.rejected_at.is_not(None))
    elif status_filter == EventStatusEnum.PAST:
        stmt = stmt.where(
            Event.rejected_at.is_(None),
            Event.ends_at <= now,
        )
    elif status_filter == EventStatusEnum.ACTIVE:
        stmt = stmt.where(
            Event.rejected_at.is_(None),
            Event.ends_at > now,
        )

    events = await session.scalars(stmt)
    return list(events.unique())


@admin_panel_router.get(
    "/{event_id}",
    response_model=EventDTO,
)
@inject
async def get_event(
    session: FromDishka[AsyncSession],
    authorized_administrator: FromDishka[AuthorizedAdministrator],
    event_id: int,
) -> Event:
    stmt = (
        select(Event)
        .where(Event.id == event_id)
        .options(selectinload(Event.participants))
    )
    event = await session.scalar(stmt)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return event


@admin_panel_router.put(
    "/{event_id}",
    response_model=EventDTO,
)
@inject
async def update_event(
    session: FromDishka[AsyncSession],
    uow_ctl: FromDishka[UoWCtl],
    authorized_administrator: FromDishka[AuthorizedAdministrator],
    notification_service: FromDishka[NotificationService],
    event_id: int,
    payload: UpdateEventDTO,
) -> Event:
    stmt = (
        select(Event)
        .where(Event.id == event_id)
        .options(selectinload(Event.participants))
    )
    event = await session.scalar(stmt)

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    raw_starts_at = update_data.get("starts_at", event.starts_at)
    raw_ends_at = update_data.get("ends_at", event.ends_at)

    if "starts_at" in update_data and raw_starts_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="starts_at cannot be null",
        )
    if "ends_at" in update_data and raw_ends_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ends_at cannot be null",
        )

    starts_at = _normalize_datetime(raw_starts_at)
    ends_at = _normalize_datetime(raw_ends_at)
    _validate_event_dates(
        starts_at=starts_at,
        ends_at=ends_at,
        created_at=event.created_at,
    )

    if "name" in update_data:
        if payload.name is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="name cannot be null",
            )
        event.name = payload.name
    if "short_description" in update_data:
        event.short_description = payload.short_description  # type: ignore[assignment]
    if "description" in update_data:
        if payload.description is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="description cannot be null",
            )
        event.description = payload.description
    if "image_url" in update_data:
        if payload.image_url is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="image_url cannot be null",
            )
        event.image_url = payload.image_url
    if "payment_info" in update_data:
        event.payment_info = payload.payment_info  # type: ignore[assignment]
    if "location" in update_data:
        event.location = payload.location  # type: ignore[assignment]
    event.starts_at = starts_at
    event.ends_at = ends_at

    if "rejected_at" in update_data:
        event.rejected_at = _normalize_datetime(payload.rejected_at) if payload.rejected_at else None  # type: ignore[arg-type]

    if "max_participants_count" in update_data:
        event.max_participants_count = payload.max_participants_count

    participant_ids = update_data.get("participants_ids")
    if participant_ids is not None:
        participant_ids = list(dict.fromkeys(participant_ids))

    max_participants_count = (
        payload.max_participants_count
        if "max_participants_count" in update_data
        else event.max_participants_count
    )

    if participant_ids is not None:
        _validate_participants_limit(
            max_participants_count,
            participant_ids,
        )
        await _ensure_users_exist(session, participant_ids)
        event.participants.clear()
        await session.flush()
        event.participants = [
            EventParticipant(
                user_id=user_id,
                status=EventParticipant.ParticipationStatusEnum.PARTICIPATING,
            )
            for user_id in participant_ids
        ]
    else:
        current_ids = [p.user_id for p in event.participants]
        _validate_participants_limit(
            max_participants_count,
            current_ids,
        )

    await session.flush()
    participant_user_ids = [
        p.user_id for p in event.participants
        if p.status == EventParticipant.ParticipationStatusEnum.PARTICIPATING
    ]
    if participant_user_ids:
        await notification_service.notify_about_event(
            EventUpdatedNotification(
                event_name=event.name,
                starts_at=event.starts_at,
                location=event.location,
                event_id=event.id,
                participants_count=len(participant_user_ids),
            ),
            recipients_ids=participant_user_ids,
        )
    await uow_ctl.commit()
    return event


@userspace_router.put(
    "/{event_id}/participants/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
async def update_my_participation(
    session: FromDishka[AsyncSession],
    uow_ctl: FromDishka[UoWCtl],
    authorized_user: FromDishka[AuthorizedUser],
    notification_service: FromDishka[NotificationService],
    event_id: int,
    payload: UpdateMyParticipationDTO,
) -> None:
    stmt_event = (select(Event)
                  .where(Event.id == event_id)
                  .options(selectinload(Event.participants)))
    event = await session.scalar(stmt_event)
    if event is None or event.rejected_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    participant = await session.scalar(
        select(EventParticipant)
        .where(EventParticipant.event_id == event_id)
        .where(EventParticipant.user_id == authorized_user.id)
    )
    original_status = participant.status if participant else None

    if payload.status == ParticipationStatusEnum.NONE:
        if participant is not None:
            await session.delete(participant)
        await session.flush()
        send_cancel = original_status == (
            EventParticipant.ParticipationStatusEnum.PARTICIPATING
        )
        if send_cancel:
            await _notify_participation_cancelled(
                session,
                notification_service,
                event,
                authorized_user.full_name,
            )
        await uow_ctl.commit()
        return None

    if payload.status is ParticipationStatusEnum.PARTICIPATING:
        ends_at = _normalize_datetime(event.ends_at)
        if ends_at <= datetime.now(tz=timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event already finished",
            )

    if payload.status is ParticipationStatusEnum.PARTICIPATING:
        stmt_count = (
            select(func.count(EventParticipant.id))
            .where(EventParticipant.event_id == event_id)
            .where(
                EventParticipant.status
                == EventParticipant.ParticipationStatusEnum.PARTICIPATING
            )
            .where(EventParticipant.user_id != authorized_user.id)
        )
        current_count = await session.scalar(stmt_count) or 0
        if (
            event.max_participants_count is not None
            and current_count + 1 > event.max_participants_count
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Max participants count exceeded",
            )

    target_status = (
        EventParticipant.ParticipationStatusEnum.PARTICIPATING
        if payload.status == ParticipationStatusEnum.PARTICIPATING
        else EventParticipant.ParticipationStatusEnum.REJECTED
    )

    if participant is None:
        participant = EventParticipant(
            event_id=event_id,
            user_id=authorized_user.id,
            status=target_status,
        )
        session.add(participant)
    else:
        participant.status = target_status

    await session.flush()
    if target_status == EventParticipant.ParticipationStatusEnum.PARTICIPATING:
        await _notify_participation_confirmed(
            session,
            notification_service,
            event,
            authorized_user.full_name,
        )
    elif (
        original_status
        == EventParticipant.ParticipationStatusEnum.PARTICIPATING
    ):
        await _notify_participation_cancelled(
            session,
            notification_service,
            event,
            authorized_user.full_name,
        )
    await uow_ctl.commit()
    return None


async def _load_admin_ids(session: AsyncSession) -> list[int]:
    stmt = (
        select(User.id)
        .where(User.role == UserRoleEnum.ADMINISTRATOR)
        .where(User.deleted_at.is_(None))
    )
    return list(await session.scalars(stmt))


async def _notify_participation_confirmed(
        session: AsyncSession,
        notification_service: NotificationService,
        event: Event,
        participant_name: str | None,
) -> None:
    admin_ids = await _load_admin_ids(session)
    if not admin_ids:
        return
    await notification_service.notify_about_event(
        EventParticipationConfirmedNotification(
            event_name=event.name,
            starts_at=event.starts_at,
            location=event.location,
            event_id=event.id,
            participants_count=_count_participating(event),
            participant_name=participant_name or "Участник",
        ),
        recipients_ids=admin_ids,
    )


async def _notify_participation_cancelled(
        session: AsyncSession,
        notification_service: NotificationService,
        event: Event,
        participant_name: str | None,
) -> None:
    admin_ids = await _load_admin_ids(session)
    if not admin_ids:
        return
    await notification_service.notify_about_event(
        EventParticipationCancelledNotification(
            event_name=event.name,
            starts_at=event.starts_at,
            location=event.location,
            event_id=event.id,
            participants_count=_count_participating(event),
            participant_name=participant_name or "Участник",
        ),
        recipients_ids=admin_ids,
    )


def _count_participating(event: Event) -> int:
    return sum(
        1
        for p in event.participants
        if p.status == EventParticipant.ParticipationStatusEnum.PARTICIPATING
    )
