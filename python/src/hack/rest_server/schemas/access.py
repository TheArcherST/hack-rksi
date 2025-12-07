from uuid import UUID

from pydantic import BaseModel


class LoginCredentials(BaseModel):
    username: str
    password: str


class AuthorizationCredentials(BaseModel):
    login_session_uid: UUID
    login_session_token: str


class Register(BaseModel):
    username: str
    password: str
