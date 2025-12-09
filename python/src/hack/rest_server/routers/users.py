from datetime import datetime, timezone

from argon2 import PasswordHasher
from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import AsyncBroker

from hack.core.models import User
from hack.core.models.user import UserRoleEnum, UserStatusEnum
from hack.core.services.uow_ctl import UoWCtl
from hack.rest_server.models import AuthorizedAdministrator
from hack.rest_server.schemas.users import (
    UserDTO,
    UpdateUserDTO,
    ResetUserPasswordDTO,
)
from hack.tasks.tasks.send_email import send_email


router = APIRouter(
    prefix="/users",
)


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


async def _get_user_or_404(
    session: AsyncSession,
    user_id: int,
) -> User:
    stmt = select(User).where(User.id == user_id)
    user = await session.scalar(stmt)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.get(
    "",
    response_model=list[UserDTO],
)
@inject
async def list_users(
    session: FromDishka[AsyncSession],
    authorized_administrator: FromDishka[AuthorizedAdministrator],
    limit: int = 50,
    full_name: str | None = None,
    role: UserRoleEnum | None = None,
    status: UserStatusEnum | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    include_deleted: bool = False,
) -> list[User]:
    limit = max(1, min(limit, 200))
    stmt = (select(User)
            .order_by(User.id)
            .limit(limit))

    if full_name:
        stmt = stmt.where(func.lower(User.full_name).like(f"%{full_name.lower()}%"))
    if role:
        stmt = stmt.where(User.role == role)
    if status is UserStatusEnum.ACTIVE:
        stmt = stmt.where(User.deleted_at.is_(None))
    elif status is UserStatusEnum.DELETED:
        stmt = stmt.where(User.deleted_at.is_not(None))
    elif not include_deleted:
        stmt = stmt.where(User.deleted_at.is_(None))

    if created_from:
        stmt = stmt.where(User.created_at >= _normalize_datetime(created_from))
    if created_to:
        stmt = stmt.where(User.created_at <= _normalize_datetime(created_to))

    users = await session.scalars(stmt)
    return list(users)


@router.put(
    "/{user_id}",
    response_model=UserDTO,
)
@inject
async def update_user(
    session: FromDishka[AsyncSession],
    uow_ctl: FromDishka[UoWCtl],
    authorized_administrator: FromDishka[AuthorizedAdministrator],
    user_id: int,
    payload: UpdateUserDTO,
) -> User:
    user = await _get_user_or_404(session, user_id)

    if payload.email and payload.email != user.email:
        stmt_conflict = (
            select(User.id)
            .where(User.email == payload.email)
            .where(User.id != user.id)
        )
        conflict_user_id = await session.scalar(stmt_conflict)
        if conflict_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists",
            )

    if payload.role:
        user.role = payload.role
    if payload.email:
        user.email = payload.email
        user.username = payload.email
    if payload.full_name:
        user.full_name = payload.full_name

    await session.flush()
    await uow_ctl.commit()
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
async def soft_delete_user(
    session: FromDishka[AsyncSession],
    uow_ctl: FromDishka[UoWCtl],
    authorized_administrator: FromDishka[AuthorizedAdministrator],
    user_id: int,
) -> None:
    user = await _get_user_or_404(session, user_id)
    user.deleted_at = datetime.now(tz=timezone.utc)
    await session.flush()
    await uow_ctl.commit()
    return None


@router.post(
    "/{user_id}/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
async def reset_user_password(
    session: FromDishka[AsyncSession],
    broker: FromDishka[AsyncBroker],
    ph: FromDishka[PasswordHasher],
    uow_ctl: FromDishka[UoWCtl],
    authorized_administrator: FromDishka[AuthorizedAdministrator],
    user_id: int,
    payload: ResetUserPasswordDTO,
) -> None:
    user = await _get_user_or_404(session, user_id)

    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reset password for deleted user",
        )

    user.password_hash = ph.hash(payload.password)
    await session.flush()
    await uow_ctl.commit()

    if payload.send_email:
        await (send_email
               .kicker()
               .with_broker(broker)
               .kiq(
                   to_email=user.email,
                   subject="Your password was reset",
                   content=(
                       "Your password was reset by an administrator.\n"
                       f"New temporary password: {payload.password}\n\n"
                       "Please log in and change it."
                   ),
               ))

    return None
