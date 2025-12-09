from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hack.core.models import IssuedRegistration
from hack.core.providers import ConfigHack
from hack.rest_server.schemas.debug import InterceptVerificationCodeDTO


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

    stmt = (
        select(IssuedRegistration)
        .order_by(IssuedRegistration.created_at.desc())
    )
    issued_registration_result = await session.scalars(stmt)
    issued_registration = issued_registration_result.first()

    if issued_registration is None:
        raise HTTPException(
            status_code=404,
            detail="No issued registrations found",
        )

    return InterceptVerificationCodeDTO(
        token=issued_registration.token,
        code=issued_registration.verification_code,
    )
