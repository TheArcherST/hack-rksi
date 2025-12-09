from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException
from taskiq import AsyncBroker

from hack.core.models import IssuedRegistration
from hack.core.services.access import (
    AccessService,
)
from hack.core.errors.access import ErrorUnauthorized, ErrorVerification, \
    ErrorEmailAlreadyExists
from hack.core.services.uow_ctl import UoWCtl
from hack.rest_server.models import AuthorizedUser
from hack.rest_server.schemas.access import (
    LoginCredentialsDTO,
    AuthorizationCredentialsDTO,
    RegisterDTO,
    ActiveLoginDTO,
    VerifyRegistrationDTO, IssuedRegistrationDTO,
)
from hack.tasks.tasks.send_email import send_email


router = APIRouter(
    prefix="",
)


@router.post(
    "/register",
    status_code=201,
    response_model=IssuedRegistrationDTO,
)
@inject
async def register(
        access_service: FromDishka[AccessService],
        uow_ctl: FromDishka[UoWCtl],
        broker: FromDishka[AsyncBroker],
        payload: RegisterDTO,
) -> IssuedRegistration:
    try:
        issued_registration = await access_service.issue_registration(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
        )
    except ErrorEmailAlreadyExists as e:
        raise HTTPException(
            status_code=400,
            detail="Email already exists",
        ) from e

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
                   f"{issued_registration.verification_code}\n\n"
                   "Enter this code to verify your account."
               ),
           ))
    return issued_registration


@router.post(
    "/register/verification",
    status_code=201,
)
@inject
async def verify_registration(
        access_service: FromDishka[AccessService],
        uow_ctl: FromDishka[UoWCtl],
        payload: VerifyRegistrationDTO,
) -> None:
    try:
        await access_service.verify_registration(
            issued_registration_token=payload.token,
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
