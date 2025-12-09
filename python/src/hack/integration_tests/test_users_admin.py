from datetime import datetime, timedelta, timezone
from uuid import uuid4

from . import api_templates
from .conftest import make_authed_client


def test_users_admin_flow(admin_client):
    # create two regular users
    user1_email = f"user1-{uuid4()}@example.com"
    user2_email = f"user2-{uuid4()}@example.com"
    make_authed_client(default_email=user1_email)
    make_authed_client(default_email=user2_email)

    # default list excludes deleted
    req = api_templates.make_list_users()
    req.params = {"limit": 200}
    r = admin_client.prepsend(req)
    assert r.status_code == 200
    users = r.json()
    user1 = next(u for u in users if u["email"] == user1_email)
    user2 = next(u for u in users if u["email"] == user2_email)
    assert user1["status"] == "ACTIVE"
    assert user2["status"] == "ACTIVE"

    user1_id = user1["id"]
    user2_id = user2["id"]

    # role filter
    req = api_templates.make_list_users()
    req.params = {"role": "USER", "limit": 200}
    r = admin_client.prepsend(req)
    assert r.status_code == 200
    assert all(item["role"] == "USER" for item in r.json())

    # registration date filter
    created_at = datetime.fromisoformat(user1["created_at"])
    req = api_templates.make_list_users()
    req.params = {
        "created_from": (created_at - timedelta(minutes=1)).isoformat(),
        "created_to": (created_at + timedelta(minutes=1)).isoformat(),
        "limit": 200,
    }
    r = admin_client.prepsend(req)
    assert r.status_code == 200
    assert any(item["email"] == user1_email for item in r.json())

    # update role and name
    req = api_templates.make_update_user()
    req.path_params = {"user_id": user1_id}
    req.json = {
        "role": "ADMINISTRATOR",
        "full_name": "Updated Name",
    }
    r = admin_client.prepsend(req)
    assert r.status_code == 200
    updated = r.json()
    assert updated["role"] == "ADMINISTRATOR"
    assert updated["full_name"] == "Updated Name"

    # soft delete second user
    req = api_templates.make_delete_user()
    req.path_params = {"user_id": user2_id}
    r = admin_client.prepsend(req)
    assert r.status_code == 204

    # deleted user not visible without include_deleted
    req = api_templates.make_list_users()
    req.params = {"limit": 200}
    r = admin_client.prepsend(req)
    assert r.status_code == 200
    assert all(item["id"] != user2_id for item in r.json())

    # deleted user returned when explicitly requested
    req = api_templates.make_list_users()
    req.params = {"include_deleted": True, "status": "DELETED", "limit": 200}
    r = admin_client.prepsend(req)
    assert r.status_code == 200
    deleted_users = [item for item in r.json() if item["id"] == user2_id]
    assert deleted_users and deleted_users[0]["status"] == "DELETED"

    # deleted user cannot login
    req = api_templates.make_login()
    req.json = {
        "email": user2_email,
        "password": "test_user_password",
    }
    r = admin_client.prepsend(req)
    assert r.status_code == 401

    # reset password for active user and login with new password
    new_password = "new_admin_password"
    req = api_templates.make_reset_user_password()
    req.path_params = {"user_id": user1_id}
    req.json = {
        "password": new_password,
        "send_email": False,
    }
    r = admin_client.prepsend(req)
    assert r.status_code == 204

    req = api_templates.make_login()
    req.json = {
        "email": user1_email,
        "password": new_password,
    }
    r = admin_client.prepsend(req)
    assert r.status_code == 201
