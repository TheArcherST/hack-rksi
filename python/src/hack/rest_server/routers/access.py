from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException

from hack.core.services.access import AccessService, ErrorUnauthorized
from hack.core.services.uow_ctl import UoWCtl
from hack.rest_server.schemas.access import LoginCredentials, \
    AuthorizationCredentials, Register

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
        payload: Register,
) -> None:
    await access_service.register(
        username=payload.username,
        password=payload.password,
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
        payload: LoginCredentials,
) -> AuthorizationCredentials:
    try:
        login_session = await access_service.login(
            username=payload.username,
            password=payload.password,
            user_agent="none",
        )
    except ErrorUnauthorized as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        ) from e

    await uow_ctl.commit()
    return AuthorizationCredentials(
        login_session_uid=login_session.uid,
        login_session_token=login_session.token,
    )
