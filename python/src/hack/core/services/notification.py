from pydantic import EmailStr
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import AsyncBroker

from hack.core.models import (
    NotificationEvent,
    User,
)
from hack.core.models.instant_notification import InstantNotification
from hack.core.models.notification_events import EventNotificationBase
from hack.core.services.email_factory import EmailFactory
from hack.tasks.tasks.send_email import send_email


class NotificationService:
    def __init__(
            self,
            session: AsyncSession,
            broker: AsyncBroker,
            email_factory: EmailFactory,
    ):
        self._session = session
        self._broker = broker
        self._email_factory = email_factory

    async def notify_about_event(
            self,
            event: NotificationEvent,
            recipients_emails: list[EmailStr] | None = None,
            recipients_ids: list[int] | None = None,
    ) -> None:
        recipients_emails = recipients_emails or []
        recipients_ids = recipients_ids or []
        if not recipients_emails and not recipients_ids:
            raise ValueError("Notification recipients must be provided")

        rendered_email = self._email_factory.build(event)

        filters = []
        if recipients_emails:
            filters.append(User.email.in_(recipients_emails))
        if recipients_ids:
            filters.append(User.id.in_(recipients_ids))

        recipients: list[User] = []
        if filters:
            stmt = select(User).where(or_(*filters))
            recipients = list(await self._session.scalars(stmt))

        extra_emails = [
            email for email in recipients_emails
            if email not in {user.email for user in recipients}
        ]

        if isinstance(event, EventNotificationBase):
            for user in recipients:
                instant_notification = InstantNotification(
                    title=rendered_email.subject,
                    content=rendered_email.content,
                    recipient_id=user.id,
                    cta_url=rendered_email.context.get("cta_url"),
                    cta_label=rendered_email.context.get("cta_label"),
                )
                self._session.add(instant_notification)

        await self._session.flush()

        all_emails = [
            *(i.email for i in recipients),
            *extra_emails,
        ]
        for i in all_emails:
            await (
                send_email.kicker()
                .with_broker(self._broker)
                .kiq(
                    to_email=i,
                    subject=rendered_email.subject,
                    content=rendered_email.content,
                    html_content=rendered_email.html_content,
                )
            )
