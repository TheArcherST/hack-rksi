from datetime import datetime

from pydantic import EmailStr

from .base import BaseDTO
from ...core.models.user import UserRoleEnum, UserStatusEnum


class UserDTO(BaseDTO):
    id: int
    role: UserRoleEnum
    email: EmailStr
    username: str
    full_name: str
    created_at: datetime
    deleted_at: datetime | None
    status: UserStatusEnum
    is_system: bool


class UpdateUserDTO(BaseDTO):
    role: UserRoleEnum | None = None
    email: EmailStr | None = None
    full_name: str | None = None


class ResetUserPasswordDTO(BaseDTO):
    password: str
    send_email: bool = False
