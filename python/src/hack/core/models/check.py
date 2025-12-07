from __future__ import annotations
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, CreatedAt


class CheckTypeEnum(StrEnum):
    PING = "PING"
    HTTP = "HTTP"
    HTTPS = "HTTPS"
    DNS = "DNS"
    TCP = "TCP"


class CheckStatusEnum(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Check(Base):
    __tablename__ = "check"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[CheckTypeEnum]
    target: Mapped[str]
    status: Mapped[CheckStatusEnum] = mapped_column(
        default=CheckStatusEnum.PENDING,
    )
    parameters: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    message: Mapped[str | None]
    started_at: Mapped[datetime | None]
    finished_at: Mapped[datetime | None]
    created_at: Mapped[CreatedAt]
