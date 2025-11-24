from __future__ import annotations

from enum import StrEnum

from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, CreatedAt


class LeadSourceTypeEnum(StrEnum):
    BOT = "BOT"


class LeadSource(Base):
    __tablename__ = "lead_source"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[LeadSourceTypeEnum] = mapped_column(default=LeadSourceTypeEnum.BOT)
    created_at: Mapped[CreatedAt]
