from datetime import datetime

from hack.core.models.appeal import AppealStatusEnum

from .base import BaseDTO


class LeadAppealDTO(BaseDTO):
    id: int
    status: AppealStatusEnum
    lead_source_id: int
    assigned_operator_id: int | None
    created_at: datetime


class LeadWithAppealsDTO(BaseDTO):
    id: int
    created_at: datetime
    appeals: list[LeadAppealDTO]


class AppealDistributionItemDTO(BaseDTO):
    lead_source_id: int
    assigned_operator_id: int | None
    appeals_count: int
