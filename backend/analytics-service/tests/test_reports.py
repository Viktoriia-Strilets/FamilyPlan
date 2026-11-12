def test_get_reports_empty(client, auth_headers):
    response = client.get(
        "/reports/",
        headers=auth_headers()
    )

    assert response.status_code == 200
    assert response.json() == []


def test_create_report_success(client, auth_headers):
    data = {
        "period": "2026-06",
        "total_spent": 8500.50,
        "recommendations_text": "Зменшити витрати на розваги"
    }

    response = client.post(
        "/reports/",
        json=data,
        headers=auth_headers()
    )

    assert response.status_code == 201

    result = response.json()

    assert result["period"] == "2026-06"
    assert result["total_spent"] == 8500.50
    assert result["family_id"] == 1
    assert result["recommendations_text"] == (
        "Зменшити витрати на розваги"
    )


def test_create_report_without_recommendations(client, auth_headers):
    data = {
        "period": "2026-07",
        "total_spent": 5000
    }

    response = client.post(
        "/reports/",
        json=data,
        headers=auth_headers()
    )

    assert response.status_code == 201
    assert response.json()["recommendations_text"] is None


def test_create_report_negative_amount(client, auth_headers):
    response = client.post(
        "/reports/",
        json={
            "period": "2026-06",
            "total_spent": -100
        },
        headers=auth_headers()
    )

    assert response.status_code == 422


def test_create_report_invalid_period(client, auth_headers):
    response = client.post(
        "/reports/",
        json={
            "period": "2026-15",
            "total_spent": 1000
        },
        headers=auth_headers()
    )

    assert response.status_code == 422


def test_get_reports_only_current_family(client, auth_headers):
    client.post(
        "/reports/",
        json={
            "period": "2026-06",
            "total_spent": 3000
        },
        headers=auth_headers(family_id=1)
    )

    client.post(
        "/reports/",
        json={
            "period": "2026-06",
            "total_spent": 7000
        },
        headers=auth_headers(family_id=2)
    )

    response = client.get(
        "/reports/",
        headers=auth_headers(family_id=1)
    )

    reports = response.json()

    assert len(reports) == 1
    assert reports[0]["family_id"] == 1
    assert reports[0]["total_spent"] == 3000


def test_delete_report_success(client, auth_headers):
    create_response = client.post(
        "/reports/",
        json={
            "period": "2026-06",
            "total_spent": 5000
        },
        headers=auth_headers()
    )

    report_id = create_response.json()["id"]

    response = client.delete(
        f"/reports/{report_id}",
        headers=auth_headers()
    )

    assert response.status_code == 200

    assert client.get(
        "/reports/",
        headers=auth_headers()
    ).json() == []


def test_delete_report_not_found(client, auth_headers):
    response = client.delete(
        "/reports/999",
        headers=auth_headers()
    )

    assert response.status_code == 404


def test_cannot_delete_another_family_report(client, auth_headers):
    create_response = client.post(
        "/reports/",
        json={
            "period": "2026-06",
            "total_spent": 5000
        },
        headers=auth_headers(family_id=1)
    )

    report_id = create_response.json()["id"]

    response = client.delete(
        f"/reports/{report_id}",
        headers=auth_headers(family_id=2)
    )

    assert response.status_code == 404


def test_reports_require_authentication(client):
    response = client.get("/reports/")

    assert response.status_code == 403