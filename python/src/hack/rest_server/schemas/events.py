from datetime import datetime

from pydantic import Field

from .base import BaseDTO
from ...core.models.event import EventStatusEnum


class EventParticipantDTO(BaseDTO):
    user_id: int
    created_at: datetime


class CreateEventDTO(BaseDTO):
    name: str
    short_description: str | None = None
    description: str
    starts_at: datetime
    ends_at: datetime
    image_url: str
    payment_info: str | None = None
    max_participants_count: int | None = Field(default=None, gt=0)
    location: str | None = None
    participants_ids: list[int] = Field(default_factory=list)


class UpdateEventDTO(BaseDTO):
    name: str | None = None
    short_description: str | None = None
    description: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    image_url: str | None = None
    payment_info: str | None = None
    max_participants_count: int | None = Field(default=None, gt=0)
    location: str | None = None
    participants_ids: list[int] | None = None
    rejected_at: datetime | None = None


class EventDTO(BaseDTO):
    id: int
    name: str
    short_description: str | None
    description: str
    starts_at: datetime
    ends_at: datetime
    image_url: str
    payment_info: str | None
    max_participants_count: int | None
    location: str | None
    created_at: datetime
    rejected_at: datetime | None
    status: EventStatusEnum
    participants: list[EventParticipantDTO]
