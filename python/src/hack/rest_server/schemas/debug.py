from uuid import UUID

from .base import BaseDTO


class InterceptVerificationCodeDTO(BaseDTO):
    token: UUID
    code: int


class InterceptRecoveryTokenDTO(BaseDTO):
    token: UUID
