from datetime import datetime

from pydantic import Field

from .base import BaseDTO


class InstantNotificationDTO(BaseDTO):
    id: int
    title: str
    content: str
    cta_url: str | None
    cta_label: str | None
    created_at: datetime
    acked_at: datetime | None


class AckInstantNotificationsDTO(BaseDTO):
    ids: list[int] = Field(default_factory=list, min_length=1)
