import pytest

from . import api_templates
from .conftest import authed_client, make_authed_client


def test_get_active_login(
        client,
        authed_client,
):
    req = api_templates.make_get_active_login()
    r = client.prepsend(req)
    assert r.status_code == 401
    r = authed_client.prepsend(req)
    assert r.status_code == 200


def _get_field_error(errors, field_name):
    for err in errors:
        loc = err.get("loc") or []
        if isinstance(loc, (list, tuple)) and loc and loc[-1] == field_name:
            return err
    return None


def test_register_rejects_invalid_email(client):
    req = api_templates.make_register()
    req.json = {
        "email": "invalid-email",
        "full_name": "sample",
        "password": "secret",
    }

    r = client.prepsend(req)

    assert r.status_code == 422
    error = _get_field_error(r.json().get("detail", []), "email")
    assert error is not None
    assert "email" in error.get("msg", "").lower()


def test_register_verification_rejects_invalid_code(client):
    req = api_templates.make_register()
    req.json = {
        "email": "test_user-invalid-code@example.com",
        "full_name": "sample",
        "password": "secret",
    }

    r = client.prepsend(req)
    assert r.status_code == 201
    token = r.json()["token"]

    req = api_templates.make_registration_verification()
    req.json = {
        "code": 111111,
        "token": token,
    }

    r = client.prepsend(req)
    assert r.status_code == 400


@pytest.mark.skip
def test_verification_manually(client):
    email = input("Email: ")
    req = api_templates.make_register()
    val_password = "test_user_password"
    req.json = {
        "email": email,
        "password": val_password,
        "full_name": "sample",
    }
    r = client.prepsend(req)
    assert r.status_code == 201
    token = r.json()["token"]
    code = input("Code: ")
    req = api_templates.make_registration_verification()
    req.json = {
        "token": token,
        "code": int(code),
    }
    r = client.prepsend(req)
    assert r.status_code == 201
    req = api_templates.make_login()
    req.json = {
        "email": email,
        "password": val_password,
    }
    r = client.prepsend(req)
    auth_creds = r.json()
    client.headers["X-Login-Session-Uid"] = auth_creds["login_session_uid"]
    client.headers["X-Login-Session-Token"] = auth_creds["login_session_token"]
    req = api_templates.make_get_active_login()
    r = client.prepsend(req)
    assert r.status_code == 200


def test_login_rejects_invalid_email(client):
    req = api_templates.make_login()
    req.json = {
        "email": "also-not-an-email",
        "full_name": "sample",
        "password": "secret",
    }

    r = client.prepsend(req)

    assert r.status_code == 422
    error = _get_field_error(r.json().get("detail", []), "email")
    assert error is not None
    assert "email" in error.get("msg", "").lower()
