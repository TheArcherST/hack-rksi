from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, CreatedAt


class UserRoleEnum(StrEnum):
    USER = "USER"
    ADMINISTRATOR = "ADMINISTRATOR"


class UserStatusEnum(StrEnum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[UserRoleEnum]
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    full_name: Mapped[str] = mapped_column()
    password_hash: Mapped[str]
    is_system: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[CreatedAt]
    deleted_at: Mapped[datetime | None]

    @property
    def status(self) -> UserStatusEnum:
        if self.deleted_at is not None:
            return UserStatusEnum.DELETED
        return UserStatusEnum.ACTIVE
