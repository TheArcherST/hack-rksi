from uuid import UUID

from .base import BaseDTO


class LoginCredentialsDTO(BaseDTO):
    username: str
    password: str


class AuthorizationCredentialsDTO(BaseDTO):
    login_session_uid: UUID
    login_session_token: str


class RegisterDTO(BaseDTO):
    username: str
    password: str


class ActiveLoginDTO(BaseDTO):
    username: str
