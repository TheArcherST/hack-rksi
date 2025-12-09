from uuid import uuid4

import pytest
from requests import Request, Session

from . import api_templates
from .base import PatchedRequest


class PatchedSession(Session):
    def prepsend(self, request: Request, **kwargs):
        kwargs.setdefault("verify", False)

        if isinstance(request, PatchedRequest):
            request.url = request.url.format(**request.path_params)

        return self.send(
            self.prepare_request(request),
            **kwargs,
        )


@pytest.fixture()
def client() -> PatchedSession:
    client = PatchedSession()
    return client


def make_authed_client(default_email: str | None = None):
    client = PatchedSession()
    req = api_templates.make_register()
    val_email = default_email or f"test_user-{uuid4()}@example.com"
    val_password = "test_user_password"
    req.json = {
        "email": val_email,
        "password": val_password,
        "full_name": "sample",
    }
    r = client.prepsend(req)
    assert r.status_code == 201
    token = r.json()["token"]

    req = api_templates.make_intercept_verification_code()
    r = client.prepsend(req)
    assert r.status_code == 200
    verification_data = r.json()
    verification_code = verification_data["code"]
    if "token" in verification_data:
        assert verification_data["token"] == token

    req = api_templates.make_registration_verification()
    req.json = {
        "code": verification_code,
        "token": token,
    }
    r = client.prepsend(req)
    assert r.status_code in (200, 201, 204)

    req = api_templates.make_login()
    req.json = {
        "email": val_email,
        "password": val_password,
    }
    r = client.prepsend(req)
    assert r.status_code == 201
    auth_creds = r.json()
    client.headers["X-Login-Session-Uid"] = auth_creds["login_session_uid"]
    client.headers["X-Login-Session-Token"] = auth_creds["login_session_token"]

    return client


@pytest.fixture()
def authed_client() -> PatchedSession:
    return make_authed_client()
