import pytest

def test_delete_budget_with_expenses_and_plans(
    client, create_budget, create_expense, auth_headers
):
    headers = auth_headers("head-delete-all@test.com", 901, "head")

    budget = create_budget(headers, amount=20000)

    actual = create_expense(
        headers,
        "Фактична витрата",
        1500,
        "2026-06-10T12:00:00",
        0,
    )

    planned = create_expense(
        headers,
        "Запланована витрата",
        3000,
        "2026-06-15T12:00:00",
        1,
    )

    response = client.delete(
        f"/budgets/{budget['id']}",
        headers=headers,
    )

    assert response.status_code == 200

    budgets = client.get("/budgets", headers=headers).json()

    assert all(b["id"] != budget["id"] for b in budgets)

    for expense in (actual, planned):
        check = client.delete(
            f"/budgets/expenses/{expense['id']}",
            headers=headers,
        )

        assert check.status_code == 404


def test_delete_one_budget_does_not_affect_other_budgets(
    client, create_budget, create_expense, auth_headers
):
    headers = auth_headers("head-delete-one@test.com", 902, "head")

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

    create_expense(
        headers,
        "Червнева витрата",
        1000,
        "2026-06-10T12:00:00",
    )

    create_expense(
        headers,
        "Липнева витрата",
        2500,
        "2026-07-10T12:00:00",
    )


    delete_response = client.delete(
            f"/budgets/{june['id']}",
            headers=headers,
        )

    assert delete_response.status_code == 200

    budgets = client.get("/budgets", headers=headers).json()

    assert len(budgets) == 1
    assert budgets[0]["id"] == july["id"]
    assert budgets[0]["total_spent"] == 2500
    assert budgets[0]["remaining_budget"] == 12500


def test_delete_nonexistent_budget_returns_404(client, auth_headers):
    headers = auth_headers("head-delete-missing@test.com", 907, "head")

    response = client.delete(
        "/budgets/999999",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Бюджет не знайдено"
