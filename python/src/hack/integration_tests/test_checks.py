from datetime import datetime

from . import api_templates


def test_checks_flow(client):
    # 1. Создание → 201
    req = api_templates.make_create_check()
    req.json = {
        "type": "PING",
        "target": "127.0.0.1",
        "parameters": {"timeout": 5},
    }
    r = client.prepsend(req)
    assert r.status_code == 201
    created = r.json()
    check_id = created["id"]
    assert created["status"] == "PENDING"
    assert created["parameters"] == {"timeout": 5}

    # 2. Список → 200
    req = api_templates.make_list_checks()
    r = client.prepsend(req)
    assert r.status_code == 200
    items = r.json()
    assert any(item["id"] == check_id for item in items)

    # 3. Получить по id → 200
    req = api_templates.make_get_check()
    req.path_params = {"check_id": check_id}
    r = client.prepsend(req)
    assert r.status_code == 200
    fetched = r.json()
    assert fetched["id"] == check_id
    assert fetched["status"] == "PENDING"

    # 4. Обновить на RUNNING → 200 и выставить started_at
    req = api_templates.make_update_check()
    req.path_params = {"check_id": check_id}
    req.json = {
        "status": "RUNNING",
        "message": "probe started",
    }
    r = client.prepsend(req)
    assert r.status_code == 200
    running = r.json()
    assert running["status"] == "RUNNING"
    assert running["message"] == "probe started"
    assert running["started_at"] is not None
    assert datetime.fromisoformat(running["started_at"]).tzinfo is not None

    # 5. Обновить на SUCCESS → 200 и выставить finished_at
    req = api_templates.make_update_check()
    req.path_params = {"check_id": check_id}
    req.json = {
        "status": "SUCCESS",
        "result": {"latency_ms": 12},
    }
    r = client.prepsend(req)
    assert r.status_code == 200
    finished = r.json()
    assert finished["status"] == "SUCCESS"
    assert finished["result"] == {"latency_ms": 12}
    assert finished["finished_at"] is not None
    assert datetime.fromisoformat(finished["finished_at"]).tzinfo is not None

    # 6. Попытка получить несуществующий → 404
    req = api_templates.make_get_check()
    req.path_params = {"check_id": check_id + 9999}
    r = client.prepsend(req)
    assert r.status_code == 404
