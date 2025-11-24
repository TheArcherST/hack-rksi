from . import api_templates


def test_lead_sources_crud(
    client,
):
    # 1. Создание → 201
    req = api_templates.make_create_lead_source()
    req.json = {
        "type": "BOT",
    }
    r = client.prepsend(req)
    assert r.status_code == 201
    data = r.json()
    lead_source_id = data["id"]
    assert data["type"] == "BOT"

    # 3. Получить список → 200
    req = api_templates.make_list_lead_sources()
    r = client.prepsend(req)
    assert r.status_code == 200
    items = r.json()
    assert any(item["id"] == lead_source_id for item in items)

    # 4. Получить по id → 200
    req = api_templates.make_get_lead_source()
    req.path_params = {"lead_source_id": lead_source_id}
    r = client.prepsend(req)
    assert r.status_code == 200
    data_get = r.json()
    assert data_get["id"] == lead_source_id

    # 5. Обновление → 200
    req = api_templates.make_update_lead_source()
    req.path_params = {"lead_source_id": lead_source_id}
    req.json = {
        "type": "BOT",  # пока менять особо нечего, но проверяем сам факт обновления
    }
    r = client.prepsend(req)
    assert r.status_code == 200

    # 6. Удаление → 204
    req = api_templates.make_delete_lead_source()
    req.path_params = {"lead_source_id": lead_source_id}
    r = client.prepsend(req)
    assert r.status_code == 204

    # 7. Повторное получение → 404
    req = api_templates.make_get_lead_source()
    req.path_params = {"lead_source_id": lead_source_id}
    r = client.prepsend(req)
    assert r.status_code == 404
