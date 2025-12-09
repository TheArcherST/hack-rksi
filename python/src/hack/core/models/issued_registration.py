from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column

from hack.core.models.base import Base, CreatedAt


class IssuedRegistration(Base):
    __tablename__ = "issued_registration"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]
    full_name: Mapped[str]
    password_hash: Mapped[str]
    verification_code: Mapped[int]
    token: Mapped[UUID]
    created_at: Mapped[CreatedAt]
