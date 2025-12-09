from uuid import UUID

from .base import BaseDTO


class InterceptVerificationCodeDTO(BaseDTO):
    token: UUID
    code: int
