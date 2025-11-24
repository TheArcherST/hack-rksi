from datetime import datetime

from hack.core.models.appeal import AppealStatusEnum

from .base import BaseDTO


class CreateAppealDTO(BaseDTO):
    lead_id: int
    lead_source_id: int


class UpdateAppealDTO(BaseDTO):
    status: AppealStatusEnum


class AppealDTO(BaseDTO):
    id: int
    status: AppealStatusEnum
    created_at: datetime

    lead_id: int
    lead_source_id: int
    assigned_operator_id: int | None
