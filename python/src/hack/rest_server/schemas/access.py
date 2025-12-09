from uuid import UUID

from pydantic import EmailStr

from .base import BaseDTO


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


class ActiveLoginDTO(BaseDTO):
    email: EmailStr
    full_name: str
