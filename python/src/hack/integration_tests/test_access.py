import pytest
from uuid import uuid4

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


def test_register_rate_limited_per_email(client):
    email = f"test_user-rate-limit-{uuid4()}@example.com"
    req = api_templates.make_register()
    req.json = {
        "email": email,
        "full_name": "sample",
        "password": "secret",
    }

    first = client.prepsend(req)
    assert first.status_code == 201
    second = client.prepsend(req)
    assert second.status_code == 201

    third = client.prepsend(req)
    assert third.status_code == 429
    retry_after = third.headers.get("Retry-After")
    assert int(retry_after) >= 60

    # Different email should still work
    req.json["email"] = f"test_user-rate-limit-{uuid4()}@example.com"
    third = client.prepsend(req)
    assert third.status_code == 201


def test_register_verification_expires(client):
    req = api_templates.make_register()
    req.json = {
        "email": "test_user-expired-code@example.com",
        "full_name": "sample",
        "password": "secret",
    }
    r = client.prepsend(req)
    assert r.status_code == 201
    token = r.json()["token"]

    req = api_templates.make_intercept_verification_code()
    r = client.prepsend(req)
    assert r.status_code == 200
    verification_data = r.json()

    expire_req = api_templates.make_expire_verification_code()
    expire_req.json = {"token": token}
    r = client.prepsend(expire_req)
    assert r.status_code == 204

    req = api_templates.make_registration_verification()
    req.json = {
        "code": verification_data["code"],
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


def test_password_recovery_flow(client):
    email = f"test_user_recovery-{uuid4()}@example.com"
    old_password = "old_secret"
    new_password = "new_secret"

    req = api_templates.make_register()
    req.json = {
        "email": email,
        "password": old_password,
        "full_name": "sample",
    }
    r = client.prepsend(req)
    assert r.status_code == 201
    registration_token = r.json()["token"]

    req = api_templates.make_intercept_verification_code()
    r = client.prepsend(req)
    assert r.status_code == 200
    verification_data = r.json()

    req = api_templates.make_registration_verification()
    req.json = {
        "code": verification_data["code"],
        "token": registration_token,
    }
    r = client.prepsend(req)
    assert r.status_code in (200, 201, 204)

    req = api_templates.make_login_recovery()
    req.json = {
        "email": email,
    }
    r = client.prepsend(req)
    assert r.status_code == 201

    req = api_templates.make_intercept_recovery_token()
    r = client.prepsend(req)
    assert r.status_code == 200
    recovery_token = r.json()["token"]

    req = api_templates.make_login_recovery_submit()
    req.json = {
        "token": recovery_token,
        "password": new_password,
    }
    r = client.prepsend(req)
    assert r.status_code == 204

    req = api_templates.make_login()
    req.json = {
        "email": email,
        "password": new_password,
    }
    r = client.prepsend(req)
    assert r.status_code == 201

    req.json = {
        "email": email,
        "password": old_password,
    }
    r = client.prepsend(req)
    assert r.status_code == 401
