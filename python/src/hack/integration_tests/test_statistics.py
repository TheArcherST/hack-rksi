from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from . import api_templates
from .conftest import make_authed_client


def test_statistics_endpoints(admin_client):
    primary_email = f"stat-user-{uuid4()}@example.com"
    secondary_email = f"stat-user-{uuid4()}@example.com"

    user_client = make_authed_client(default_email=primary_email)
    make_authed_client(default_email=secondary_email)

    req = api_templates.make_list_users()
    req.params = {"limit": 200}
    r = admin_client.prepsend(req)
    assert r.status_code == 200
    users_by_email = {item["email"]: item for item in r.json()}
    user_id = users_by_email[primary_email]["id"]
    secondary_id = users_by_email[secondary_email]["id"]

    now = datetime.now(tz=timezone.utc)
    starts_at = now + timedelta(hours=1)
    ends_at = starts_at + timedelta(hours=2)

    req = api_templates.make_create_event()
    req.json = {
        "name": "Stat event A",
        "short_description": "insights",
        "description": "Event with two participants",
        "starts_at": starts_at.isoformat(),
        "ends_at": ends_at.isoformat(),
        "image_url": "https://example.com/stat-a.png",
        "payment_info": "none",
        "max_participants_count": 5,
        "participants_ids": [user_id, secondary_id],
    }
    r = admin_client.prepsend(req)
    assert r.status_code == 201

    req = api_templates.make_create_event()
    req.json = {
        "name": "Stat event B",
        "short_description": "insights",
        "description": "Empty event for histogram",
        "starts_at": (starts_at + timedelta(hours=1)).isoformat(),
        "ends_at": (ends_at + timedelta(hours=1)).isoformat(),
        "image_url": "https://example.com/stat-b.png",
        "payment_info": None,
        "participants_ids": [],
    }
    r = admin_client.prepsend(req)
    assert r.status_code == 201
    event_b_id = r.json()["id"]

    req = api_templates.make_create_event()
    req.json = {
        "name": "Stat event C",
        "short_description": "insights",
        "description": "Half-filled event",
        "starts_at": (starts_at + timedelta(hours=2)).isoformat(),
        "ends_at": (ends_at + timedelta(hours=2)).isoformat(),
        "image_url": "https://example.com/stat-c.png",
        "payment_info": None,
        "max_participants_count": 2,
        "participants_ids": [user_id],
    }
    r = admin_client.prepsend(req)
    assert r.status_code == 201

    req = api_templates.make_update_my_participation()
    req.path_params = {"event_id": event_b_id}
    req.json = {"status": "REJECTED"}
    r = user_client.prepsend(req)
    assert r.status_code == 204

    req = api_templates.make_get_my_statistics()
    r = user_client.prepsend(req)
    assert r.status_code == 200
    user_stats = r.json()
    assert user_stats["total_events"] == 3
    assert user_stats["active_events"] == 3
    assert user_stats["participating_events"] == 2
    assert user_stats["rejected_events"] == 0
    assert user_stats["upcoming_participations"] == 2
    assert abs(user_stats["participation_rate"] - (2 / 3)) < 0.01

    pytest.skip(reason="Rest of statistics test relays on clean instance")

    req = api_templates.make_get_admin_statistics()
    r = admin_client.prepsend(req)
    assert r.status_code == 200
    stats = r.json()

    scalars = {item["name"]: item["value"] for item in stats["scalars"]}
    assert scalars["events_total"] == 3
    assert scalars["active_events"] == 3
    assert scalars["total_participations"] == 3
    assert scalars["unique_participants"] == 2
    assert scalars["avg_participants_per_event"] == 1

    graphs = {item["name"]: item["points"] for item in stats["graphs"]}
    assert graphs["events_by_start_date"]
    assert graphs["events_by_start_date"][0]["y"] == 3
    assert graphs["participants_by_start_date"][0]["y"] == 3

    histograms = {item["name"]: item["bins"] for item in stats["histograms"]}
    participants_bins = {item["label"]: item["count"] for item in histograms["participants_per_event"]}
    assert participants_bins["0"] == 1
    assert participants_bins["1"] == 1
    assert participants_bins["2-3"] == 1

    fill_rate_bins = {item["label"]: item["count"] for item in histograms["capacity_fill_rate"]}
    assert fill_rate_bins["25-50%"] == 1
    assert fill_rate_bins["50-75%"] == 1
