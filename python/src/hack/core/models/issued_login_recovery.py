from __future__ import annotations

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from hack.core.models.base import Base, CreatedAt


class IssuedLoginRecovery(Base):
    __tablename__ = "issued_login_recovery"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    token: Mapped[UUID] = mapped_column(default=uuid.uuid4, unique=True)
    created_at: Mapped[CreatedAt]
    used_at: Mapped[datetime | None]
