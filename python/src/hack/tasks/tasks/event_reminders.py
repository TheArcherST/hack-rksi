from __future__ import annotations

from datetime import datetime, timedelta, timezone
from logging import getLogger

from dishka import FromDishka
from dishka.integrations.taskiq import inject
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from hack.core.models import Event, EventParticipant
from hack.core.models.notification_events import EventReminderNotification
from hack.core.services.notification import NotificationService
from hack.core.services.uow_ctl import UoWCtl
from hack.tasks.brokers.default import default_broker

logger = getLogger(__name__)


@default_broker.task(schedule=[{"cron": "*/1 * * * *"}])
@inject(patch_module=True)
async def queue_event_reminders(
        session: FromDishka[AsyncSession],
        notification_service: FromDishka[NotificationService],
        uow_ctl: FromDishka[UoWCtl],
) -> None:
    logger.info("Performing scheduled revision of event reminders")
    now = datetime.now(tz=timezone.utc)
    horizon = now + timedelta(hours=24)

    stmt = (
        select(EventParticipant)
        .join(Event)
        .options(
            (selectinload(EventParticipant.event)
             .selectinload(Event.participants)),
            selectinload(EventParticipant.user),
        )
        .where(EventParticipant.status
               == EventParticipant.ParticipationStatusEnum.PARTICIPATING)
        .where(EventParticipant.reminder_queued_at.is_(None))
        .where(Event.rejected_at.is_(None))
        .where(Event.starts_at <= horizon)
        .where(Event.starts_at >= now)
    )
    participants = list(await session.scalars(stmt))
    if not participants:
        return

    for participant in participants:
        event = participant.event
        participants_count = sum(
            1
            for p in event.participants
            if p.status == EventParticipant.ParticipationStatusEnum.PARTICIPATING
        )
        await notification_service.notify_about_event(
            EventReminderNotification(
                event_name=event.name,
                starts_at=event.starts_at,
                location=event.location,
                event_id=event.id,
                participants_count=participants_count,
                recipient_name=participant.user.full_name,
            ),
            recipients_ids=[participant.user_id],
        )
        participant.reminder_queued_at = now

    await session.flush()
    await uow_ctl.commit()
