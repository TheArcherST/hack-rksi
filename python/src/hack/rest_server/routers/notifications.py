from datetime import datetime, timezone

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hack.core.models.instant_notification import InstantNotification
from hack.core.services.uow_ctl import UoWCtl
from hack.rest_server.models import AuthorizedUser
from hack.rest_server.schemas.notifications import (
    AckInstantNotificationsDTO,
    InstantNotificationDTO,
)

router = APIRouter(
    prefix="/notifications",
)


@router.get(
    "/instant",
    response_model=list[InstantNotificationDTO],
)
@inject
async def list_instant_notifications(
    session: FromDishka[AsyncSession],
    authorized_user: FromDishka[AuthorizedUser],
    include_acked: bool = Query(default=False),
) -> list[InstantNotification]:
    stmt = (
        select(InstantNotification)
        .where(InstantNotification.recipient_id == authorized_user.id)
        .order_by(InstantNotification.created_at.desc())
    )
    if not include_acked:
        stmt = stmt.where(InstantNotification.acked_at.is_(None))

    notifications = await session.scalars(stmt)
    return list(notifications)


@router.post(
    "/instant/ack",
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
async def ack_instant_notifications(
    session: FromDishka[AsyncSession],
    uow_ctl: FromDishka[UoWCtl],
    authorized_user: FromDishka[AuthorizedUser],
    payload: AckInstantNotificationsDTO,
) -> None:
    unique_ids = list(dict.fromkeys(payload.ids))
    if not unique_ids:
        return None

    stmt = (
        select(InstantNotification)
        .where(InstantNotification.recipient_id == authorized_user.id)
        .where(InstantNotification.id.in_(unique_ids))
    )
    notifications = list(await session.scalars(stmt))
    found_ids = {n.id for n in notifications}
    missing = set(unique_ids) - found_ids
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    now = datetime.now(tz=timezone.utc)
    for notification in notifications:
        if notification.acked_at is None:
            notification.acked_at = now

    await session.flush()
    await uow_ctl.commit()
    return None
