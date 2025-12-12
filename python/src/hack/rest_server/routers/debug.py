from datetime import datetime, timedelta, timezone

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from hack.core.models import IssuedRegistration, IssuedLoginRecovery, User, \
    Event
from hack.core.providers import ConfigHack
from hack.core.services.access import AccessService
from hack.core.services.uow_ctl import UoWCtl
from hack.rest_server.schemas.debug import (
    InterceptVerificationCodeDTO,
    InterceptRecoveryTokenDTO,
    ChangeUserRoleDTO,
    ExpireVerificationCodeDTO,
)

router = APIRouter(
    prefix="/debug",
    include_in_schema=False,
)


@router.get(
    "/intercept-verification-code",
    response_model=InterceptVerificationCodeDTO,
)
@inject
async def intercept_verification_code(
        session: FromDishka[AsyncSession],
        config: FromDishka[ConfigHack],
) -> InterceptVerificationCodeDTO:
    if not config.debug:
        raise HTTPException(status_code=404, detail="Not found")

    stmt = (select(IssuedRegistration)
            .order_by(IssuedRegistration.created_at.desc()))
    issued_registration = await session.scalar(stmt)

    if issued_registration is None:
        raise HTTPException(
            status_code=404,
            detail="No issued registrations found",
        )

    return InterceptVerificationCodeDTO(
        token=issued_registration.token,
        code=issued_registration.verification_code,
    )


@router.get(
    "/intercept-recovery-token",
    response_model=InterceptRecoveryTokenDTO,
)
@inject
async def intercept_verification_code(
        session: FromDishka[AsyncSession],
        config: FromDishka[ConfigHack],
) -> InterceptRecoveryTokenDTO:
    if not config.debug:
        raise HTTPException(status_code=404, detail="Not found")

    stmt = (select(IssuedLoginRecovery)
            .order_by(IssuedLoginRecovery.created_at.desc()))
    issued_login_recovery = await session.scalar(stmt)

    if issued_login_recovery is None:
        raise HTTPException(
            status_code=404,
            detail="No issued registrations found",
        )

    return InterceptRecoveryTokenDTO(
        token=issued_login_recovery.token,
    )


@router.post(
    "/expire-verification-code",
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
async def expire_verification_code(
        session: FromDishka[AsyncSession],
        uow_ctl: FromDishka[UoWCtl],
        config: FromDishka[ConfigHack],
        payload: ExpireVerificationCodeDTO,
) -> None:
    if not config.debug:
        raise HTTPException(status_code=404, detail="Not found")

    stmt = (
        select(IssuedRegistration)
        .where(IssuedRegistration.token == payload.token)
        .order_by(IssuedRegistration.created_at.desc())
    )
    issued_registration = await session.scalar(stmt)
    if issued_registration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issued registration not found",
        )

    issued_registration.created_at = (
        datetime.now(tz=timezone.utc)
        - AccessService.REGISTRATION_VERIFICATION_TTL
        - timedelta(minutes=1)
    )
    await session.flush()
    await uow_ctl.commit()
    return None


@router.post(
    "/delete-examples",
)
@inject
async def delete_examples(
        session: FromDishka[AsyncSession],
        uow: FromDishka[UoWCtl],
) -> None:
    stmt = (delete(User)
            .where(User.email.endswith("@example.com")))
    await session.execute(stmt)
    stmt = (delete(Event)
            .where(Event.image_url.startswith("https://example.com/")))
    await session.execute(stmt)
    await uow.commit()


@router.post(
    "/change-role",
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
async def change_user_role(
        session: FromDishka[AsyncSession],
        uow_ctl: FromDishka[UoWCtl],
        config: FromDishka[ConfigHack],
        payload: ChangeUserRoleDTO,
) -> None:
    if not config.debug:
        raise HTTPException(status_code=404, detail="Not found")

    stmt = (select(User)
            .where(User.email == payload.email))
    user = await session.scalar(stmt)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.role = payload.role
    await session.flush()
    await uow_ctl.commit()
    return None
