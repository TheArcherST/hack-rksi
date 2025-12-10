from uuid import UUID

from pydantic import EmailStr

from .base import BaseDTO
from ...core.models.user import UserRoleEnum


class InterceptVerificationCodeDTO(BaseDTO):
    token: UUID
    code: int


class InterceptRecoveryTokenDTO(BaseDTO):
    token: UUID


class ChangeUserRoleDTO(BaseDTO):
    email: EmailStr
    role: UserRoleEnum


class ExpireVerificationCodeDTO(BaseDTO):
    token: UUID
