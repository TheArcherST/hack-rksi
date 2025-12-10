from datetime import datetime, timedelta, timezone
from uuid import uuid4

from hack.integration_tests import api_templates
from hack.integration_tests.conftest import make_authed_client


def test_notifications_flow(admin_client):
    # Registration events (confirm + welcome) triggered by account creation and verification
    primary_email = f"notif-primary-{uuid4()}@example.com"
    secondary_email = f"notif-secondary-{uuid4()}@example.com"
    primary_client = make_authed_client(default_email=primary_email)
    secondary_client = make_authed_client(default_email=secondary_email)

    # Password recovery flow (reset link + password changed)
    req = api_templates.make_login_recovery()
    req.json = {"email": primary_email}
    r = primary_client.prepsend(req)
    assert r.status_code == 201

    req = api_templates.make_intercept_recovery_token()
    r = primary_client.prepsend(req)
    assert r.status_code == 200
    recovery_token = r.json()["token"]

    req = api_templates.make_login_recovery_submit()
    req.json = {"token": recovery_token, "password": "new-secret"}
    r = primary_client.prepsend(req)
    assert r.status_code == 204

    # Discover user ids
    req = api_templates.make_list_users()
    req.params = {"limit": 200}
    r = admin_client.prepsend(req)
    assert r.status_code == 200
    users_by_email = {u["email"]: u["id"] for u in r.json()}
    primary_id = users_by_email[primary_email]
    secondary_id = users_by_email[secondary_email]

    starts_at = datetime.now(tz=timezone.utc) + timedelta(hours=2)
    ends_at = starts_at + timedelta(hours=1)

    # Event created (notifies participants)
    req = api_templates.make_create_event()
    req.json = {
        "name": "Notification Test Event",
        "short_description": "short",
        "description": "desc",
        "starts_at": starts_at.isoformat(),
        "ends_at": ends_at.isoformat(),
        "image_url": "https://example.com/image.png",
        "participants_ids": [primary_id],
    }
    r = admin_client.prepsend(req)
    assert r.status_code == 201
    event_id = r.json()["id"]

    # Event updated
    req = api_templates.make_update_event()
    req.path_params = {"event_id": event_id}
    req.json = {"name": "Updated Notification Test Event"}
    r = admin_client.prepsend(req)
    assert r.status_code == 200

    # Participation confirmed (secondary joins)
    req = api_templates.make_update_my_participation()
    req.path_params = {"event_id": event_id}
    req.json = {"status": "PARTICIPATING"}
    r = secondary_client.prepsend(req)
    assert r.status_code == 204

    # Participation cancelled (secondary leaves)
    req.json = {"status": "NONE"}
    r = secondary_client.prepsend(req)
    assert r.status_code == 204

    # Admin sets password for secondary user (admin set password)
    req = api_templates.make_reset_user_password()
    req.path_params = {"user_id": secondary_id}
    req.json = {"password": "temp-pass", "send_email": True}
    r = admin_client.prepsend(req)
    assert r.status_code == 204

    _expected_types = {
        "REG_CONFIRM_CODE",
        "REG_WELCOME",
        "PASSWORD_RESET_LINK",
        "PASSWORD_CHANGED",
        "EVENT_CREATED",
        "EVENT_UPDATED",
        "EVENT_PARTICIPATION_CONFIRMED",
        "EVENT_PARTICIPATION_CANCELLED",
        "ADMIN_SET_PASSWORD",
    }
    # todo: verify
