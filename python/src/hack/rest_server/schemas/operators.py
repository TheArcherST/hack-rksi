from datetime import datetime

from hack.core.models.operator import OperatorStatusEnum

from .base import BaseDTO


class CreateOperatorDTO(BaseDTO):
    status: OperatorStatusEnum
    active_appeals_limit: int


class UpdateOperatorDTO(BaseDTO):
    status: OperatorStatusEnum
    active_appeals_limit: int


class OperatorDTO(BaseDTO):
    id: int
    status: OperatorStatusEnum
    active_appeals_limit: int
    created_at: datetime
