import pytest

def test_budget_with_date_range_filtering(
    client, create_budget, create_expense, auth_headers
):
    headers = auth_headers("mom@bud.com", 404, "head")

    create_budget(headers, amount=20000)

    create_expense(
        headers,
        title="June Purchase",
        amount=4000,
        date="2026-06-15T12:00:00",
    )

    outside_response = client.post(
        "/budgets/expenses",
        json={
            "title": "July Purchase",
            "amount": 5000,
            "category": "Покупки",
            "is_planned": 0,
            "date": "2026-07-05T12:00:00",
        },
        headers=headers,
    )

    assert outside_response.status_code == 400

    summary = client.get("/budgets", headers=headers).json()[0]

    assert summary["total_spent"] == 4000
    assert summary["remaining_budget"] == 16000


def test_members_can_add_expenses_and_plans(
    client, create_budget, create_expense, auth_headers
):
    head_headers = auth_headers("head@bud.com", 777, "head")
    member_headers = auth_headers("member@bud.com", 777, "member")

    create_budget(
        head_headers,
        amount=10000,
        start="2026-03-01T00:00:00",
        end="2026-03-31T23:59:59",
    )

    create_expense(
        member_headers,
        title="Продукти",
        amount=1200,
        date="2026-03-10T12:00:00",
        is_planned=0,
    )

    create_expense(
        member_headers,
        title="Ремонт",
        amount=4000,
        date="2026-03-15T12:00:00",
        is_planned=1,
    )

    response = client.get("/budgets", headers=member_headers)

    assert response.status_code == 200
    summary = response.json()[0]

    assert summary["total_spent"] == 1200
    assert summary["total_planned_expenses"] == 4000
    assert summary["remaining_budget"] == 8800


def test_delete_expense_from_one_period_keeps_budgets_intact(
    client, create_budget, create_expense, auth_headers
):
    headers = auth_headers("head-delete-expense@test.com", 906, "head")

    june = create_budget(
        headers,
        10000,
        "2026-06-01T00:00:00",
        "2026-06-30T23:59:59",
    )

    july = create_budget(
        headers,
        15000,
        "2026-07-01T00:00:00",
        "2026-07-31T23:59:59",
    )

    july_expense = create_expense(
        headers,
        "Липнева витрата",
        2500,
        "2026-07-10T12:00:00",
    )

    delete_response = client.delete(
        f"/budgets/expenses/{july_expense['id']}",
        headers=headers,
    )

    assert delete_response.status_code == 200

    response = client.get("/budgets", headers=headers)

    assert response.status_code == 200
    budgets = response.json()

    assert len(budgets) == 2
    assert {b["id"] for b in budgets} == {june["id"], july["id"]}

    july_summary = next(
        b for b in budgets if b["id"] == july["id"]
    )

    assert july_summary["total_spent"] == 0
    assert july_summary["remaining_budget"] == 15000
