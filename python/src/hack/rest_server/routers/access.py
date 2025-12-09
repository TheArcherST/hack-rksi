from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException
from taskiq import AsyncBroker

from hack.core.services.access import (
    AccessService,
)
from hack.core.errors.access import ErrorUnauthorized
from hack.core.errors.verification import ErrorVerification
from hack.core.services.verification import VerificationService
from hack.core.services.uow_ctl import UoWCtl
from hack.rest_server.models import AuthorizedUser
from hack.rest_server.schemas.access import (
    LoginCredentialsDTO,
    AuthorizationCredentialsDTO,
    RegisterDTO,
    RegisterVerificationDTO,
    ActiveLoginDTO,
)
from hack.tasks.tasks.send_email import send_email


router = APIRouter(
    prefix="",
)


@router.post(
    "/register",
    status_code=201,
)
@inject
async def register(
        access_service: FromDishka[AccessService],
        verification_service: FromDishka[VerificationService],
        uow_ctl: FromDishka[UoWCtl],
        broker: FromDishka[AsyncBroker],
        payload: RegisterDTO,
) -> None:
    user = await access_service.register(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
    )
    code = await verification_service.issue_code(user)
    await uow_ctl.commit()
    await (send_email
           .kicker()
           .with_broker(broker)
           .kiq(
               to_email=payload.email,
               subject="Verify your Hack account",
               content=(
                   f"Hello, {payload.full_name}!\n\n"
                   "Here is your verification code:\n"
                   f"{code}\n\n"
                   "Enter this code to verify your account."
               ),
           ))
    return None


@router.post(
    "/register/verification",
    status_code=204,
)
@inject
async def verify_registration(
        verification_service: FromDishka[VerificationService],
        uow_ctl: FromDishka[UoWCtl],
        payload: RegisterVerificationDTO,
) -> None:
    try:
        await verification_service.verify_by_code(
            email=payload.email,
            code=payload.code,
        )
    except ErrorVerification as e:
        raise HTTPException(
            status_code=400,
            detail="Invalid verification code",
        ) from e

    await uow_ctl.commit()
    return None


@router.post(
    "/login",
    status_code=201,
)
@inject
async def login(
        access_service: FromDishka[AccessService],
        uow_ctl: FromDishka[UoWCtl],
        payload: LoginCredentialsDTO,
) -> AuthorizationCredentialsDTO:
    try:
        login_session = await access_service.login(
            email=payload.email,
            password=payload.password,
            user_agent="none",
        )
    except ErrorUnauthorized as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        ) from e

    await uow_ctl.commit()
    return AuthorizationCredentialsDTO(
        login_session_uid=login_session.uid,
        login_session_token=login_session.token,
    )


@router.get(
    "/login",
    response_model=ActiveLoginDTO,
)
@inject
async def get_active_login(
        authorized_user: FromDishka[AuthorizedUser],
):
    return authorized_user
