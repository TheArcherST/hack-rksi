import uuid
from typing import AsyncGenerator, Any, NewType
from uuid import UUID

import aioboto3
from dishka import Provider, Scope, from_context, provide
from fastapi import FastAPI, HTTPException
from fastapi.requests import Request
from starlette.testclient import TestClient

from hack.core.providers import ConfigS3
from hack.core.services.access import AccessService
from hack.core.errors.access import ErrorUnauthorized
from hack.rest_server.models import (
    AuthorizedUser,
    CurrentLoginSession,
    AuthorizedAdministrator,
)
from hack.core.models.user import UserRoleEnum


S3Client = NewType("S3Client", object)


class ProviderServer(Provider):
    app = from_context(FastAPI, scope=Scope.SESSION)
    request = from_context(provides=Request, scope=Scope.REQUEST)

    @provide(scope=Scope.SESSION, cache=False)
    def get_test_client(self, app: FastAPI) -> TestClient:
        return TestClient(app)

    @provide(scope=Scope.REQUEST)
    async def get_current_login_session(
            self,
            request: Request,
            access_service: AccessService,
    ) -> CurrentLoginSession:
        login_session_uid = request.headers.get(
            "X-Login-Session-Uid",
            str(uuid.uuid4()),
        )
        login_session_uid = UUID(login_session_uid)
        login_session_token = request.headers.get(
            "X-Login-Session-Token",
            "stub-token",
        )

        try:
            login_session = await access_service.lookup_login_session(
                login_session_uid=login_session_uid,
                login_session_token=login_session_token,
            )
        except ErrorUnauthorized as e:
            raise HTTPException(
                status_code=401,
                detail="Invalid login session",
            ) from e

        return CurrentLoginSession(login_session)

    @provide(scope=Scope.REQUEST)
    async def get_authorized_user(
            self,
            current_login_session: CurrentLoginSession,
    ) -> AuthorizedUser:
        user = current_login_session.user
        if user.deleted_at is not None:
            raise HTTPException(
                status_code=403,
                detail="User deleted",
            )
        return AuthorizedUser(user)

    @provide(scope=Scope.REQUEST)
    async def get_authorized_administrator(
            self,
            authorized_user: AuthorizedUser,
    ) -> AuthorizedAdministrator:
        if (
            authorized_user.role != UserRoleEnum.ADMINISTRATOR
            and not authorized_user.is_system
        ):
            raise HTTPException(
                status_code=403,
                detail="Administrator role required",
            )
        return AuthorizedAdministrator(authorized_user)

    get_access_service = provide(
        AccessService,
        scope=Scope.REQUEST,
    )

    @provide(scope=Scope.APP)
    async def get_s3_client(
            self,
            config: ConfigS3,
    ) -> AsyncGenerator[S3Client, None]:
        session = aioboto3.Session()
        async with session.client(
                "s3",
                endpoint_url=config.endpoint_url,
                aws_access_key_id=config.access_key,
                aws_secret_access_key=config.secret_key,
                region_name=config.region_name,
        ) as client:
            yield client
