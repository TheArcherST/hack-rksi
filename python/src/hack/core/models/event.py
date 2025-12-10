from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, CreatedAt

if TYPE_CHECKING:
    from .user import User


class EventStatusEnum(StrEnum):
    ACTIVE = "ACTIVE"
    PAST = "PAST"
    REJECTED = "REJECTED"


class Event(Base):
    __tablename__ = "event"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    short_description: Mapped[str | None]
    description: Mapped[str]
    starts_at: Mapped[datetime]
    ends_at: Mapped[datetime]
    image_url: Mapped[str]
    payment_info: Mapped[str | None] = mapped_column(Text)
    max_participants_count: Mapped[int | None]
    location: Mapped[str | None]
    created_at: Mapped[CreatedAt]
    rejected_at: Mapped[datetime | None]

    participants: Mapped[list["EventParticipant"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )

    @property
    def status(self) -> EventStatusEnum:
        if self.rejected_at is not None:
            return EventStatusEnum.REJECTED

        ends_at = self.ends_at
        if ends_at.tzinfo is None:
            ends_at = ends_at.replace(tzinfo=timezone.utc)

        now = datetime.now(tz=timezone.utc)
        if ends_at <= now:
            return EventStatusEnum.PAST
        return EventStatusEnum.ACTIVE


class EventParticipant(Base):
    __tablename__ = "event_participant"
    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="event_participant_unique"),
    )

    class ParticipationStatusEnum(StrEnum):
        PARTICIPATING = "PARTICIPATING"
        REJECTED = "REJECTED"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[CreatedAt]
    status: Mapped[ParticipationStatusEnum]
    reminder_queued_at: Mapped[datetime | None]

    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))

    event: Mapped[Event] = relationship(back_populates="participants")
    user: Mapped[User] = relationship()
