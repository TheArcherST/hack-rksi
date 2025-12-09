from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, CreatedAt
from .user import User


class InstantNotification(Base):
    __tablename__ = "instant_notification"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()
    acked_at: Mapped[datetime | None]
    created_at: Mapped[CreatedAt]

    recipient_id: Mapped[int] = mapped_column(ForeignKey("user.id"))

    recipient: Mapped[User] = relationship()
