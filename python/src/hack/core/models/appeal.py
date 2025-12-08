from __future__ import annotations

from typing import TYPE_CHECKING
from enum import StrEnum

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, CreatedAt

if TYPE_CHECKING:
    from . import Operator


class AppealStatusEnum(StrEnum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"


class Appeal(Base):
    __tablename__ = "appeal"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[AppealStatusEnum]
    created_at: Mapped[CreatedAt]

    lead_id: Mapped[int] = mapped_column(ForeignKey("lead.id"))
    lead_source_id: Mapped[int] = mapped_column(ForeignKey("lead_source.id"))
    assigned_operator_id: Mapped[int | None] = mapped_column(
        ForeignKey("operator.id"))

    assigned_operator: Mapped[Operator] = relationship()
