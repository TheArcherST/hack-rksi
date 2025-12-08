from time import sleep

from . import api_templates


def test_appeals_routing_respects_weights_and_limits(
        client,
):
    """
    Интеграционный тест роутинга обращений:

    - создаём источник;
    - создаём двух операторов:
        op1: ACTIVE, limit=1
        op2: ACTIVE, limit=100
    - привязываем их к источнику с весами:
        op1: routing_factor = 1_000_000_000 (очень большой)
        op2: routing_factor = 1
    - создаём пачку обращений для одного и того же lead_id;
    - проверяем:
        * лимит op1 соблюдён (не более 1 активного обращения);
        * оба оператора получили обращения;
        * подавляющее большинство обращений ушло на op2 после того,
          как op1 набрал свой лимит;
        * данные в /inspect сходятся с проведёнными операциями
    """

    # ---------- 1. Создаём lead source ----------
    req = api_templates.make_create_lead_source()
    req.json = {
        "type": "BOT",
    }
    r = client.prepsend(req)
    assert r.status_code == 201
    lead_source = r.json()
    lead_source_id = lead_source["id"]

    # ---------- 2. Создаём операторов ----------
    # op1: маленький лимит, огромный вес
    req = api_templates.make_create_operator()
    req.json = {
        "status": "ACTIVE",
        "active_appeals_limit": 1,
    }
    r = client.prepsend(req)
    assert r.status_code == 201
    op1 = r.json()
    op1_id = op1["id"]

    # op2: большой лимит, маленький вес
    req = api_templates.make_create_operator()
    req.json = {
        "status": "ACTIVE",
        "active_appeals_limit": 100,
    }
    r = client.prepsend(req)
    assert r.status_code == 201
    op2 = r.json()
    op2_id = op2["id"]

    # ---------- 3. Привязываем операторов к источнику с весами ----------
    # op1: очень большой routing_factor
    req = api_templates.make_create_lead_source_operator()
    req.path_params = {"lead_source_id": lead_source_id}
    req.json = {
        "operator_id": op1_id,
        "routing_factor": 1_000_000_000,
    }
    r = client.prepsend(req)
    assert r.status_code == 201

    # op2: маленький routing_factor
    req = api_templates.make_create_lead_source_operator()
    req.path_params = {"lead_source_id": lead_source_id}
    req.json = {
        "operator_id": op2_id,
        "routing_factor": 1,
    }
    r = client.prepsend(req)
    assert r.status_code == 201

    # ---------- 4. Создаём пачку обращений ----------
    lead_id = 1
    appeals_to_create = 20

    for _ in range(appeals_to_create):
        req = api_templates.make_create_appeal()
        req.json = {
            "lead_id": lead_id,
            "lead_source_id": lead_source_id,
        }
        r = client.prepsend(req)
        assert r.status_code == 201

    # ---------- 5. Анализируем распределение по /appeals ----------

    # ждём немного, чтобы задачи в очереди выполнились
    sleep(1.5)

    req = api_templates.make_list_appeals()
    r = client.prepsend(req)
    assert r.status_code == 200
    appeals = r.json()

    # Фильтруем только обращения по нашему источнику
    appeals = [
        a for a in appeals
        if a["lead_source_id"] == lead_source_id
    ]
    assert len(appeals) == appeals_to_create

    # Считаем, сколько обращений досталось каждому оператору
    count_by_operator: dict[int, int] = {}
    for a in appeals:
        operator_id = a["assigned_operator_id"]
        # Ожидаем, что оператор всегда назначен
        assert operator_id is not None
        count_by_operator[operator_id] = count_by_operator.get(operator_id, 0) + 1

    op1_count = count_by_operator.get(op1_id, 0)
    op2_count = count_by_operator.get(op2_id, 0)

    # ---------- 6. Проверяем лимиты и распределение ----------

    # Лимит operator1 = 1 → он не должен иметь больше одного активного обращения
    assert op1_count <= 1, f"Operator1 got {op1_count} appeals, but limit is 1"

    # Все обращения должны быть распределены между двумя операторами
    assert op1_count + op2_count == appeals_to_create

    # Operator2 должен получить все остальные обращения
    assert op2_count >= appeals_to_create - 1

    # При таком перекосе весов почти наверняка хотя бы одно обращение уйдёт на op1.
    assert op1_count >= 1, "Expected operator1 to be chosen at least once"
    assert op2_count >= 1, "Expected operator2 to be chosen at least once"

    # ---------- 7. Сверка через /inspect/leads ----------
    req = api_templates.make_inspect_leads()
    r = client.prepsend(req)
    assert r.status_code == 200
    leads = r.json()

    # Находим нужного лида
    lead_item = next((l for l in leads if l["id"] == lead_id), None)
    assert lead_item is not None, f"Lead {lead_id} not found in /inspect/leads"

    # Берём только обращения этого лида по нашему источнику
    inspected_appeals = [
        a for a in lead_item.get("appeals", [])
        if a["lead_source_id"] == lead_source_id
    ]
    assert len(inspected_appeals) == appeals_to_create

    # Пересчитываем распределение по операторам из /inspect/leads
    inspected_counts: dict[int, int] = {}
    for a in inspected_appeals:
        operator_id = a["assigned_operator_id"]
        assert operator_id is not None
        inspected_counts[operator_id] = inspected_counts.get(operator_id, 0) + 1

    inspected_op1_count = inspected_counts.get(op1_id, 0)
    inspected_op2_count = inspected_counts.get(op2_id, 0)

    assert inspected_op1_count == op1_count
    assert inspected_op2_count == op2_count

    # ---------- 8. Сверка через /inspect/appeals-distribution ----------
    req = api_templates.make_inspect_appeals_distribution()
    r = client.prepsend(req)
    assert r.status_code == 200
    distribution = r.json()

    def find_dist(lead_source_id_: int, operator_id_: int | None) -> int | None:
        for item in distribution:
            if (
                item["lead_source_id"] == lead_source_id_
                and item["assigned_operator_id"] == operator_id_
            ):
                return item["appeals_count"]
        return None

    dist_op1 = find_dist(lead_source_id, op1_id)
    dist_op2 = find_dist(lead_source_id, op2_id)

    # Ожидаем, что в агрегатах есть записи для обоих операторов
    assert dist_op1 is not None, "No distribution record for operator1 in /inspect/appeals-distribution"
    assert dist_op2 is not None, "No distribution record for operator2 in /inspect/appeals-distribution"

    assert dist_op1 == op1_count
    assert dist_op2 == op2_count
