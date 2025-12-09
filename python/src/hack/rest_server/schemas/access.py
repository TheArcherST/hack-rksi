from uuid import UUID

from pydantic import EmailStr

from .base import BaseDTO
from ...core.models.user import UserRoleEnum


class LoginCredentialsDTO(BaseDTO):
    email: EmailStr
    password: str


class AuthorizationCredentialsDTO(BaseDTO):
    login_session_uid: UUID
    login_session_token: str


class RegisterDTO(BaseDTO):
    email: EmailStr
    password: str
    full_name: str


class IssuedRegistrationDTO(BaseDTO):
    token: UUID


class ActiveLoginDTO(BaseDTO):
    role: UserRoleEnum
    email: EmailStr
    full_name: str


class VerifyRegistrationDTO(BaseDTO):
    token: UUID
    code: int


class LoginRecoveryRequestDTO(BaseDTO):
    email: EmailStr


class IssuedLoginRecoveryDTO(BaseDTO):
    pass


class LoginRecoverySubmitDTO(BaseDTO):
    token: UUID
    password: str
