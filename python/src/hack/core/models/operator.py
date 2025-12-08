from enum import StrEnum

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, CreatedAt


class OperatorStatusEnum(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Operator(Base):
    __tablename__ = "operator"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[OperatorStatusEnum]
    active_appeals: Mapped[int]
    active_appeals_limit: Mapped[int]
    created_at: Mapped[CreatedAt]


class LeadSourceOperator(Base):
    __tablename__ = "lead_source_operator"

    id: Mapped[int] = mapped_column(primary_key=True)
    routing_factor: Mapped[int]
    created_at: Mapped[CreatedAt]

    operator_id: Mapped[int] = mapped_column(ForeignKey("operator.id"))
    lead_source_id: Mapped[int] = mapped_column(ForeignKey("lead_source.id"))
