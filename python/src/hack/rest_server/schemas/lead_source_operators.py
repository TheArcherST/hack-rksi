from datetime import datetime

from .base import BaseDTO


class CreateLeadSourceOperatorDTO(BaseDTO):
    operator_id: int
    routing_factor: int


class UpdateLeadSourceOperatorDTO(BaseDTO):
    routing_factor: int


class LeadSourceOperatorDTO(BaseDTO):
    id: int
    created_at: datetime

    operator_id: int
    lead_source_id: int
    routing_factor: int
