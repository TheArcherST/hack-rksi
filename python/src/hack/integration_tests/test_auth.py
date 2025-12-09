from uuid import uuid4

from . import api_templates


def test_auth(
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


def test_register_verification_rejects_invalid_code(authed_client):
    req = api_templates.make_verification()
    req.json = {
        "code": 111111,
    }

    r = authed_client.prepsend(req)
    assert r.status_code == 400


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
