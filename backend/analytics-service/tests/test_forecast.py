from app.models import ExpenseReportModel


def test_forecast_without_reports(client, auth_headers):
    response = client.get(
        "/analytics/forecast",
        headers=auth_headers()
    )

    assert response.status_code == 200

    result = response.json()

    assert result["period"] == "Наступний місяць"
    assert result["predicted_amount"] == 10500.0


def test_forecast_with_one_report(client, db, auth_headers):
    db.add(
        ExpenseReportModel(
            family_id=1,
            period="2026-06",
            total_spent=8000
        )
    )

    db.commit()

    response = client.get(
        "/analytics/forecast",
        headers=auth_headers()
    )

    assert response.status_code == 200

    result = response.json()

    assert result["predicted_amount"] == 8400.0


def test_forecast_with_multiple_reports(client, db, auth_headers):
    db.add_all([
        ExpenseReportModel(
            family_id=1,
            period="2026-04",
            total_spent=10000
        ),
        ExpenseReportModel(
            family_id=1,
            period="2026-05",
            total_spent=12000
        )
    ])

    db.commit()

    response = client.get(
        "/analytics/forecast",
        headers=auth_headers()
    )

    assert response.status_code == 200

    result = response.json()

    # Середнє: (10000 + 12000) / 2 = 11000
    # Тренд: 12000 / 10000 = 1.2
    # Прогноз: 11000 * ((1.2 + 1) / 2) = 12100

    assert result["predicted_amount"] == 12100.0


def test_forecast_ignores_other_families(client, db, auth_headers):
    db.add_all([
        ExpenseReportModel(
            family_id=1,
            period="2026-04",
            total_spent=10000
        ),
        ExpenseReportModel(
            family_id=1,
            period="2026-05",
            total_spent=12000
        ),
        ExpenseReportModel(
            family_id=2,
            period="2026-04",
            total_spent=50000
        ),
        ExpenseReportModel(
            family_id=2,
            period="2026-05",
            total_spent=60000
        )
    ])

    db.commit()

    response = client.get(
        "/analytics/forecast",
        headers=auth_headers(family_id=1)
    )

    assert response.status_code == 200
    assert response.json()["predicted_amount"] == 12100.0


def test_forecast_require_authentication(client):
    response = client.get("/analytics/forecast")

    assert response.status_code == 403