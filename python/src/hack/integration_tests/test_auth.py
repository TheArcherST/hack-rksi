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
