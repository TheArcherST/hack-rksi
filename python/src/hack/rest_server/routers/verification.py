from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import HTTPException

from hack.core.errors.verification import ErrorVerification
from hack.core.services.uow_ctl import UoWCtl
from hack.core.services.verification import VerificationService
from hack.rest_server.routers.access import router
from hack.rest_server.schemas.verification import VerificationDTO
from hack.rest_server.models import AuthorizedUser


@router.post(
    "/verification",
    status_code=204,
)
@inject
async def verify_registration(
        verification_service: FromDishka[VerificationService],
        uow_ctl: FromDishka[UoWCtl],
        authorized_user: FromDishka[AuthorizedUser],
        payload: VerificationDTO,
) -> None:
    try:
        await verification_service.verify_by_code(
            email=authorized_user.email,
            code=payload.code,
        )
    except ErrorVerification as e:
        raise HTTPException(
            status_code=400,
            detail="Invalid verification code",
        ) from e

    await uow_ctl.commit()
    return None
