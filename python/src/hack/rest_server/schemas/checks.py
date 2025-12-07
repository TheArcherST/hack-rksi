from datetime import datetime
from typing import Any

from hack.core.models import CheckStatusEnum, CheckTypeEnum

from .base import BaseDTO


class CreateCheckDTO(BaseDTO):
    type: CheckTypeEnum
    target: str
    parameters: dict[str, Any] | None = None


class CheckDTO(BaseDTO):
    id: int
    type: CheckTypeEnum
    target: str
    status: CheckStatusEnum
    parameters: dict[str, Any] | None
    result: dict[str, Any] | None
    message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class UpdateCheckDTO(BaseDTO):
    status: CheckStatusEnum | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    message: str | None = None
    result: dict[str, Any] | None = None
