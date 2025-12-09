from datetime import datetime, timedelta, timezone
from uuid import uuid4

from . import api_templates
from .conftest import make_authed_client


def test_events_crud(admin_client):
    participant1_email = f"participant1-{uuid4()}@example.com"
    participant2_email = f"participant2-{uuid4()}@example.com"
    make_authed_client(default_email=participant1_email)
    make_authed_client(default_email=participant2_email)

    # fetch participant ids through admin list
    req = api_templates.make_list_users()
    req.params = {"include_deleted": True, "limit": 200}
    r = admin_client.prepsend(req)
    assert r.status_code == 200
    users_by_email = {item["email"]: item["id"] for item in r.json()}
    participant1_id = users_by_email[participant1_email]
    participant2_id = users_by_email[participant2_email]

    starts_at = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    ends_at = starts_at + timedelta(hours=2)

    # create event
    req = api_templates.make_create_event()
    req.json = {
        "name": "Sample event",
        "short_description": "Short info",
        "description": "Detailed description",
        "starts_at": starts_at.isoformat(),
        "ends_at": ends_at.isoformat(),
        "image_url": "https://example.com/image.png",
        "payment_info": "Send cash",
        "max_participants_count": 2,
        "location": "Main hall",
        "participants_ids": [participant1_id],
    }
    r = admin_client.prepsend(req)
    assert r.status_code == 201
    event = r.json()
    event_id = event["id"]
    assert event["status"] == "ACTIVE"
    assert len(event["participants"]) == 1

    # updating with too many participants is rejected
    req = api_templates.make_update_event()
    req.path_params = {"event_id": event_id}
    req.json = {
        "max_participants_count": 1,
        "participants_ids": [participant1_id, participant2_id],
    }
    r = admin_client.prepsend(req)
    assert r.status_code == 400

    # update event, add participant and reject
    req = api_templates.make_update_event()
    req.path_params = {"event_id": event_id}
    req.json = {
        "name": "Updated name",
        "description": "Updated description",
        "participants_ids": [participant1_id, participant2_id],
        "max_participants_count": 2,
        "rejected_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    r = admin_client.prepsend(req)
    assert r.status_code == 200
    updated = r.json()
    assert updated["status"] == "REJECTED"
    assert len(updated["participants"]) == 2

    # get event and ensure filters work
    req = api_templates.make_get_event()
    req.path_params = {"event_id": event_id}
    r = admin_client.prepsend(req)
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Updated name"

    req = api_templates.make_list_events()
    req.params = {"status": "REJECTED"}
    r = admin_client.prepsend(req)
    assert r.status_code == 200
    assert any(item["id"] == event_id for item in r.json())
