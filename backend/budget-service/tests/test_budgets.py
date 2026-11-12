import pytest

def test_budget_creation_and_remaining_calculation(
    client, create_budget, create_expense, auth_headers
):
    headers = auth_headers("dad@bud.com", 101, "head")

    create_budget(headers, amount=10000)

    create_expense(
        headers,
        title="Supermarket",
        amount=2500,
        date="2026-06-15T12:00:00",
    )

    response = client.get("/budgets", headers=headers)

    assert response.status_code == 200
    summary = response.json()[0]

    assert summary["total_spent"] == 2500
    assert summary["remaining_budget"] == 7500


def test_budget_update_and_expense_deletion(
    client, create_budget, create_expense, auth_headers
):
    headers = auth_headers("head@bud.com", 303, "head")

    budget = create_budget(
        headers,
        amount=5000,
        start="2026-01-01T00:00:00",
        end="2026-01-31T23:59:59",
    )

    budget_id = budget["id"]

    update_response = client.put(
        f"/budgets/{budget_id}",
        json={
            "total_planned_budget": 12000,
            "currency": "USD",
            "start_date": "2026-01-01T00:00:00",
            "end_date": "2026-01-31T23:59:59",
        },
        headers=headers,
    )

    assert update_response.status_code == 200

    expense = create_expense(
        headers,
        title="Expense",
        amount=1500,
        date="2026-01-10T12:00:00",
    )

    summary = client.get("/budgets", headers=headers).json()[0]
    assert summary["remaining_budget"] == 10500

    delete_response = client.delete(
        f"/budgets/expenses/{expense['id']}",
        headers=headers,
    )

    assert delete_response.status_code == 200

    summary_after = client.get("/budgets", headers=headers).json()[0]

    assert summary_after["total_spent"] == 0
    assert summary_after["remaining_budget"] == 12000


def test_get_budgets_only_returns_current_family(
    client, create_budget, auth_headers
):
    family_a = auth_headers("head-a@test.com", 1001, "head")
    family_b = auth_headers("head-b@test.com", 1002, "head")

    create_budget(family_a, amount=10000)
    create_budget(family_b, amount=20000)

    response = client.get("/budgets", headers=family_a)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["family_id"] == 1001

@pytest.mark.parametrize(
    "amount",
    [0, -100, -1]
)
def test_budget_cannot_have_zero_or_negative_amount(
    client,
    auth_headers,
    amount,
):
    headers = auth_headers(
        "invalid-budget@test.com",
        1234,
        "head",
    )

    response = client.post(
        "/budgets",
        headers=headers,
        json={
            "total_planned_budget": amount,
            "start_date": "2026-06-01T00:00:00",
            "end_date": "2026-06-30T23:59:59",
        },
    )

    assert response.status_code == 422