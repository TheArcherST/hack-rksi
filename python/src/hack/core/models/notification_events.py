from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AnyUrl, BaseModel, EmailStr, Field


class NotificationEventTypeEnum(StrEnum):
    REG_CONFIRM_CODE = "REG_CONFIRM_CODE"
    REG_WELCOME = "REG_WELCOME"
    PASSWORD_RESET_LINK = "PASSWORD_RESET_LINK"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    EVENT_CREATED = "EVENT_CREATED"
    EVENT_UPDATED = "EVENT_UPDATED"
    EVENT_REMINDER = "EVENT_REMINDER"
    EVENT_PARTICIPATION_CONFIRMED = "EVENT_PARTICIPATION_CONFIRMED"
    EVENT_PARTICIPATION_CANCELLED = "EVENT_PARTICIPATION_CANCELLED"
    ADMIN_SET_PASSWORD = "ADMIN_SET_PASSWORD"


class NotificationEventBase(BaseModel):
    type: NotificationEventTypeEnum


class RegistrationConfirmCodeEvent(NotificationEventBase):
    type: Literal[NotificationEventTypeEnum.REG_CONFIRM_CODE] = (
        NotificationEventTypeEnum.REG_CONFIRM_CODE
    )
    full_name: str
    verification_code: int


class RegistrationWelcomeEvent(NotificationEventBase):
    type: Literal[NotificationEventTypeEnum.REG_WELCOME] = (
        NotificationEventTypeEnum.REG_WELCOME
    )
    full_name: str


class PasswordResetLinkEvent(NotificationEventBase):
    type: Literal[NotificationEventTypeEnum.PASSWORD_RESET_LINK] = (
        NotificationEventTypeEnum.PASSWORD_RESET_LINK
    )
    full_name: str | None = None
    reset_url: AnyUrl
    expires_at: datetime | None = None


class PasswordChangedEvent(NotificationEventBase):
    type: Literal[NotificationEventTypeEnum.PASSWORD_CHANGED] = (
        NotificationEventTypeEnum.PASSWORD_CHANGED
    )
    full_name: str | None = None


class EventNotificationBase(NotificationEventBase):
    event_name: str
    starts_at: datetime
    location: str | None = None
    event_id: int | None = None
    event_url: AnyUrl | str | None = None
    recipient_name: str | None = None
    participants_count: int | None = None


class EventCreatedNotification(EventNotificationBase):
    type: Literal[NotificationEventTypeEnum.EVENT_CREATED] = (
        NotificationEventTypeEnum.EVENT_CREATED
    )
    organizer_name: str | None = None


class EventUpdatedNotification(EventNotificationBase):
    type: Literal[NotificationEventTypeEnum.EVENT_UPDATED] = (
        NotificationEventTypeEnum.EVENT_UPDATED
    )
    updates_summary: str | None = None


class EventReminderNotification(EventNotificationBase):
    type: Literal[NotificationEventTypeEnum.EVENT_REMINDER] = (
        NotificationEventTypeEnum.EVENT_REMINDER
    )
    hours_before: int = 24


class EventParticipationConfirmedNotification(EventNotificationBase):
    type: Literal[NotificationEventTypeEnum.EVENT_PARTICIPATION_CONFIRMED] = (
        NotificationEventTypeEnum.EVENT_PARTICIPATION_CONFIRMED
    )
    participant_name: str


class EventParticipationCancelledNotification(EventNotificationBase):
    type: Literal[NotificationEventTypeEnum.EVENT_PARTICIPATION_CANCELLED] = (
        NotificationEventTypeEnum.EVENT_PARTICIPATION_CANCELLED
    )
    participant_name: str


class AdminSetPasswordNotification(NotificationEventBase):
    type: Literal[NotificationEventTypeEnum.ADMIN_SET_PASSWORD] = (
        NotificationEventTypeEnum.ADMIN_SET_PASSWORD
    )
    email: EmailStr
    full_name: str | None = None
    temporary_password: str
    admin_name: str | None = None


NotificationEvent = Annotated[
    RegistrationConfirmCodeEvent
    | RegistrationWelcomeEvent
    | PasswordResetLinkEvent
    | PasswordChangedEvent
    | EventCreatedNotification
    | EventUpdatedNotification
    | EventReminderNotification
    | EventParticipationConfirmedNotification
    | EventParticipationCancelledNotification
    | AdminSetPasswordNotification,
    Field(discriminator="type"),
]


class RenderedEmail(BaseModel):
    subject: str
    html_content: str
    content: str
