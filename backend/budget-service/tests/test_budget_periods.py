import pytest


def test_create_multiple_budget_periods(
    client, create_budget, auth_headers
):
    headers = auth_headers("head-multiple@test.com", 888, "head")

    create_budget(
        headers,
        amount=10000,
        start="2026-06-01T00:00:00",
        end="2026-06-30T23:59:59",
    )

    create_budget(
        headers,
        amount=15000,
        start="2026-07-01T00:00:00",
        end="2026-07-31T23:59:59",
    )

    response = client.get("/budgets", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_budget_period_overlap_forbidden(
    client, create_budget, auth_headers
):
    headers = auth_headers("head-overlap@test.com", 889, "head")

    create_budget(
        headers,
        amount=10000,
        start="2026-06-01T00:00:00",
        end="2026-06-30T23:59:59",
    )

    overlap = client.post(
        "/budgets",
        json={
            "total_planned_budget": 12000,
            "start_date": "2026-06-15T00:00:00",
            "end_date": "2026-07-15T23:59:59",
        },
        headers=headers,
    )

    assert overlap.status_code == 400


def test_expenses_are_counted_only_in_own_period(
    client, create_budget, create_expense, auth_headers
):
    headers = auth_headers("head-periods@test.com", 890, "head")

    create_budget(
        headers,
        amount=10000,
        start="2026-06-01T00:00:00",
        end="2026-06-30T23:59:59",
    )

    create_budget(
        headers,
        amount=15000,
        start="2026-07-01T00:00:00",
        end="2026-07-31T23:59:59",
    )

    create_expense(
        headers, "June", 2000, "2026-06-15T12:00:00"
    )

    create_expense(
        headers, "July", 5000, "2026-07-10T12:00:00"
    )

    response = client.get("/budgets", headers=headers)

    assert response.status_code == 200
    budgets = response.json()

    june = next(
        b for b in budgets
        if b["start_date"].startswith("2026-06")
    )

    july = next(
        b for b in budgets
        if b["start_date"].startswith("2026-07")
    )

    assert june["total_spent"] == 2000
    assert july["total_spent"] == 5000
    assert june["remaining_budget"] == 8000
    assert july["remaining_budget"] == 10000


def test_update_one_budget_not_affect_another(
    client, create_budget, auth_headers
):
    headers = auth_headers("head-update-period@test.com", 891, "head")

    create_budget(
        headers,
        amount=10000,
        start="2026-06-01T00:00:00",
        end="2026-06-30T23:59:59",
    )

    create_budget(
        headers,
        amount=20000,
        start="2026-07-01T00:00:00",
        end="2026-07-31T23:59:59",
    )

    budgets = client.get("/budgets", headers=headers).json()

    june_id = next(
        b["id"] for b in budgets
        if b["start_date"].startswith("2026-06")
    )

    update = client.put(
        f"/budgets/{june_id}",
        json={
            "total_planned_budget": 30000,
            "currency": "USD",
            "start_date": "2026-06-01T00:00:00",
            "end_date": "2026-06-30T23:59:59",
        },
        headers=headers,
    )

    assert update.status_code == 200

    after = client.get("/budgets", headers=headers).json()

    june = next(
        b for b in after
        if b["start_date"].startswith("2026-06")
    )

    july = next(
        b for b in after
        if b["start_date"].startswith("2026-07")
    )

    assert june["total_planned_budget"] == 30000
    assert july["total_planned_budget"] == 20000
