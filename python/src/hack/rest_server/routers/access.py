from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException

from hack.core.services.access import AccessService, ErrorUnauthorized
from hack.core.services.uow_ctl import UoWCtl
from hack.rest_server.models import AuthorizedUser
from hack.rest_server.schemas.access import (
    LoginCredentialsDTO,
    AuthorizationCredentialsDTO,
    RegisterDTO,
    ActiveLoginDTO,
)


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
        uow_ctl: FromDishka[UoWCtl],
        payload: RegisterDTO,
) -> None:
    await access_service.register(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
    )
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
