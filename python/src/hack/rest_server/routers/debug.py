from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hack.core.models import IssuedRegistration, IssuedLoginRecovery
from hack.core.providers import ConfigHack
from hack.rest_server.schemas.debug import (
    InterceptVerificationCodeDTO,
    InterceptRecoveryTokenDTO,
)

router = APIRouter(
    prefix="/debug",
    include_in_schema=True,  # todo: exclude
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
