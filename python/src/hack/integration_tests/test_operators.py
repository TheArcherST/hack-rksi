from . import api_templates


def test_operators_crud(
    client,
):
    # 1. Создание → 201
    req = api_templates.make_create_operator()
    req.json = {
        "status": "ACTIVE",
        "active_appeals_limit": 5,
    }
    r = client.prepsend(req)
    assert r.status_code == 201
    data = r.json()
    operator_id = data["id"]
    assert data["status"] == "ACTIVE"
    assert data["active_appeals_limit"] == 5

    # 3. Список операторов → 200
    req = api_templates.make_list_operators()
    r = client.prepsend(req)
    assert r.status_code == 200
    items = r.json()
    assert any(item["id"] == operator_id for item in items)

    # 4. Получить по id → 200
    req = api_templates.make_get_operator()
    req.path_params = {"operator_id": operator_id}
    r = client.prepsend(req)
    assert r.status_code == 200
    data_get = r.json()
    assert data_get["id"] == operator_id

    # 5. Обновление → 200
    req = api_templates.make_update_operator()
    req.path_params = {"operator_id": operator_id}
    req.json = {
        "status": "INACTIVE",
        "active_appeals_limit": 10,
    }
    r = client.prepsend(req)
    assert r.status_code == 200
    data_updated = r.json()
    assert data_updated["status"] == "INACTIVE"
    assert data_updated["active_appeals_limit"] == 10

    # 6. Удаление → 204
    req = api_templates.make_delete_operator()
    req.path_params = {"operator_id": operator_id}
    r = client.prepsend(req)
    assert r.status_code == 204

    # 7. Повторное получение → 404
    req = api_templates.make_get_operator()
    req.path_params = {"operator_id": operator_id}
    r = client.prepsend(req)
    assert r.status_code == 404
