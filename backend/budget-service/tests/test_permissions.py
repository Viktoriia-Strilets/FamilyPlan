import pytest

def test_only_head_can_create_budget(client, auth_headers):
    family_id = 555

    head_headers = auth_headers(
        "head@test.com", family_id, "head"
    )

    member_headers = auth_headers(
        "member@test.com", family_id, "member"
    )

    payload = {
        "total_planned_budget": 10000,
        "start_date": "2026-03-01T00:00:00",
        "end_date": "2026-03-31T23:59:59",
    }

    forbidden = client.post(
        "/budgets",
        json=payload,
        headers=member_headers,
    )

    assert forbidden.status_code == 403

    success = client.post(
        "/budgets",
        json=payload,
        headers=head_headers,
    )

    assert success.status_code == 200


def test_only_head_can_delete_budget(
    client, create_budget, auth_headers
):
    head_headers = auth_headers(
        "head-delete-permission@test.com", 903, "head"
    )

    member_headers = auth_headers(
        "member-delete-permission@test.com", 903, "member"
    )

    budget = create_budget(
        head_headers,
        amount=12000,
        start="2026-08-01T00:00:00",
        end="2026-08-31T23:59:59",
    )

    response = client.delete(
        f"/budgets/{budget['id']}",
        headers=member_headers,
    )

    assert response.status_code == 403

    check = client.get("/budgets", headers=head_headers)

    assert check.status_code == 200
    assert any(
        b["id"] == budget["id"]
        for b in check.json()
    )


def test_user_cannot_delete_budget_from_another_family(
    client, create_budget, auth_headers
):
    family_a_headers = auth_headers(
        "head-family-a@test.com", 904, "head"
    )

    family_b_headers = auth_headers(
        "head-family-b@test.com", 905, "head"
    )

    budget = create_budget(
        family_a_headers,
        amount=18000,
        start="2026-09-01T00:00:00",
        end="2026-09-30T23:59:59",
    )

    response = client.delete(
        f"/budgets/{budget['id']}",
        headers=family_b_headers,
    )

    assert response.status_code == 404

    check = client.get(
        "/budgets",
        headers=family_a_headers,
    )

    assert check.status_code == 200
    assert any(
        b["id"] == budget["id"]
        for b in check.json()
    )
