import csv
import io
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from openpyxl import load_workbook

from . import api_templates
from .conftest import make_authed_client


def test_export_event_participants_csv_and_xlsx(admin_client):
    participant_email = f"participant-{uuid4()}@example.com"
    rejected_email = f"rejected-{uuid4()}@example.com"
    participant_client = make_authed_client(default_email=participant_email)
    rejected_client = make_authed_client(default_email=rejected_email)

    req = api_templates.make_list_users()
    req.params = {"limit": 200}
    r = admin_client.prepsend(req)
    assert r.status_code == 200
    users_by_email = {item["email"]: item for item in r.json()}
    participant_id = users_by_email[participant_email]["id"]
    rejected_id = users_by_email[rejected_email]["id"]

    now = datetime.now(tz=timezone.utc)
    starts_at = now + timedelta(hours=1)
    ends_at = starts_at + timedelta(hours=2)

    req = api_templates.make_create_event()
    req.json = {
        "name": "Export event",
        "short_description": "export",
        "description": "Testing export",
        "starts_at": starts_at.isoformat(),
        "ends_at": ends_at.isoformat(),
        "image_url": "https://example.com/export.png",
        "payment_info": None,
        "participants_ids": [participant_id, rejected_id],
    }
    r = admin_client.prepsend(req)
    assert r.status_code == 201
    event_id = r.json()["id"]

    req = api_templates.make_update_my_participation()
    req.path_params = {"event_id": event_id}
    req.json = {"status": "REJECTED"}
    r = rejected_client.prepsend(req)
    assert r.status_code == 204

    req = api_templates.make_export_event_participants()
    req.path_params = {"event_id": event_id}
    req.params = {"format": "csv"}
    r = admin_client.prepsend(req)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    reader = csv.reader(io.StringIO(r.content.decode()))
    rows = list(reader)
    assert rows[0] == [
        "user_id",
        "email",
        "full_name",
        "status",
        "joined_at",
        "event_id",
        "event_name",
    ]
    data_rows = rows[1:]
    assert len(data_rows) == 1
    assert data_rows[0][1] == participant_email

    req = api_templates.make_export_event_participants()
    req.path_params = {"event_id": event_id}
    req.params = {"format": "xlsx"}
    r = admin_client.prepsend(req)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    workbook = load_workbook(io.BytesIO(r.content))
    sheet = workbook.active
    values = list(sheet.values)
    assert values[0] == (
        "user_id",
        "email",
        "full_name",
        "status",
        "joined_at",
        "event_id",
        "event_name",
    )
    data_rows = values[1:]
    emails = [row[1] for row in data_rows]
    assert participant_email in emails
    assert rejected_email not in emails
