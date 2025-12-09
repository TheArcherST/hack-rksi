from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

from . import api_templates


def test_upload_file_requires_auth(client):
    req = api_templates.make_upload_file()
    req.files = {"file": ("sample.png", b"fake-bytes", "image/png")}

    r = client.prepsend(req)

    assert r.status_code == 401


def test_upload_file_returns_public_url(authed_client):
    req = api_templates.make_upload_file()
    req.files = {"file": ("sample.png", b"first-image-bytes", "image/png")}
    r = authed_client.prepsend(req)
    assert r.status_code == 201
    first_url = r.json()["url"]
    _assert_uploaded_url(first_url)

    req = api_templates.make_upload_file()
    req.files = {"file": ("sample.png", b"second-image-bytes", "image/png")}
    r = authed_client.prepsend(req)
    assert r.status_code == 201
    second_url = r.json()["url"]
    _assert_uploaded_url(second_url)

    assert first_url != second_url


def _assert_uploaded_url(url: str):
    parsed = urlparse(url)
    assert parsed.scheme in ("http", "https")
    assert parsed.netloc

    path = Path(parsed.path)
    assert "events" in path.parts
    assert path.suffix == ".png"

    UUID(path.stem)
