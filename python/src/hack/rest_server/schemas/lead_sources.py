from datetime import datetime

from hack.core.models.lead_source import LeadSourceTypeEnum

from .base import BaseDTO


class CreateLeadSourceDTO(BaseDTO):
    type: LeadSourceTypeEnum


class UpdateLeadSourceDTO(BaseDTO):
    # note: I think that type editing must be prohibited
    pass


class LeadSourceDTO(BaseDTO):
    id: int
    type: LeadSourceTypeEnum
    created_at: datetime
