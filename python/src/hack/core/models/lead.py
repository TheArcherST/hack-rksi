from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .appeal import Appeal

from .base import Base, CreatedAt


class Lead(Base):
    __tablename__ = "lead"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[CreatedAt]

    appeals: Mapped[list[Appeal]] = relationship()
