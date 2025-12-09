from datetime import datetime, timedelta, timezone

from . import api_templates


def test_event_cards_and_participation(admin_client, authed_client):
    starts_at = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    ends_at = starts_at + timedelta(hours=2)

    # Admin creates event
    req = api_templates.make_create_event()
    req.json = {
        "name": "User event",
        "short_description": "card",
        "description": "Full description",
        "starts_at": starts_at.isoformat(),
        "ends_at": ends_at.isoformat(),
        "image_url": "https://example.com/image.png",
        "payment_info": "none",
        "participants_ids": [],
    }
    r = admin_client.prepsend(req)
    assert r.status_code == 201
    event_id = r.json()["id"]

    # User sees card with NONE status
    req = api_templates.make_list_event_cards()
    r = authed_client.prepsend(req)
    assert r.status_code == 200
    cards = [c for c in r.json() if c["id"] == event_id]
    assert cards
    card = cards[0]
    assert card["participation_status"] == "NONE"
    assert card["participants_count"] == 0

    # Join event
    req = api_templates.make_update_my_participation()
    req.path_params = {"event_id": event_id}
    req.json = {"status": "PARTICIPATING"}
    r = authed_client.prepsend(req)
    assert r.status_code == 204

    req = api_templates.make_list_event_cards()
    r = authed_client.prepsend(req)
    card = next(c for c in r.json() if c["id"] == event_id)
    assert card["participation_status"] == "PARTICIPATING"
    assert card["participants_count"] == 1

    # Reject event
    req = api_templates.make_update_my_participation()
    req.path_params = {"event_id": event_id}
    req.json = {"status": "REJECTED"}
    r = authed_client.prepsend(req)
    assert r.status_code == 204

    req = api_templates.make_list_event_cards()
    r = authed_client.prepsend(req)
    card = next(c for c in r.json() if c["id"] == event_id)
    assert card["participation_status"] == "REJECTED"
    assert card["participants_count"] == 0

    # Leave event (NONE)
    req = api_templates.make_update_my_participation()
    req.path_params = {"event_id": event_id}
    req.json = {"status": "NONE"}
    r = authed_client.prepsend(req)
    assert r.status_code == 204

    req = api_templates.make_list_event_cards()
    r = authed_client.prepsend(req)
    card = next(c for c in r.json() if c["id"] == event_id)
    assert card["participation_status"] == "NONE"
    assert card["participants_count"] == 0

    # Hide rejected events from users
    req = api_templates.make_update_event()
    req.path_params = {"event_id": event_id}
    req.json = {
        "rejected_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    r = admin_client.prepsend(req)
    assert r.status_code == 200

    req = api_templates.make_list_event_cards()
    r = authed_client.prepsend(req)
    assert all(c["id"] != event_id for c in r.json())
