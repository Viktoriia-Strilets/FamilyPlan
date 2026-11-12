from app.models import CategoryStatisticsModel


def test_categories_empty(client, auth_headers):
    response = client.get(
        "/analytics/categories/2026-06",
        headers=auth_headers()
    )

    assert response.status_code == 200
    assert response.json() == []


def test_categories_statistics(client, db, auth_headers):
    db.add_all([
        CategoryStatisticsModel(
            family_id=1,
            category="Продукти",
            total_amount=3000,
            period="2026-06"
        ),
        CategoryStatisticsModel(
            family_id=1,
            category="Комунальні послуги",
            total_amount=2000,
            period="2026-06"
        ),
        CategoryStatisticsModel(
            family_id=1,
            category="Розваги",
            total_amount=1000,
            period="2026-06"
        )
    ])

    db.commit()

    response = client.get(
        "/analytics/categories/2026-06",
        headers=auth_headers()
    )

    assert response.status_code == 200

    result = {
        item["category"]: item
        for item in response.json()
    }

    assert len(result) == 3

    assert result["Продукти"]["total_amount"] == 3000
    assert result["Продукти"]["percentage"] == 50.0

    assert result["Комунальні послуги"]["percentage"] == 33.33

    assert result["Розваги"]["percentage"] == 16.67


def test_categories_only_current_period(client, db, auth_headers):
    db.add_all([
        CategoryStatisticsModel(
            family_id=1,
            category="Продукти",
            total_amount=3000,
            period="2026-06"
        ),
        CategoryStatisticsModel(
            family_id=1,
            category="Продукти",
            total_amount=5000,
            period="2026-07"
        )
    ])

    db.commit()

    response = client.get(
        "/analytics/categories/2026-06",
        headers=auth_headers()
    )

    result = response.json()

    assert len(result) == 1
    assert result[0]["total_amount"] == 3000


def test_categories_family_isolation(client, db, auth_headers):
    db.add_all([
        CategoryStatisticsModel(
            family_id=1,
            category="Продукти",
            total_amount=3000,
            period="2026-06"
        ),
        CategoryStatisticsModel(
            family_id=2,
            category="Продукти",
            total_amount=9000,
            period="2026-06"
        )
    ])

    db.commit()

    response = client.get(
        "/analytics/categories/2026-06",
        headers=auth_headers(family_id=1)
    )

    result = response.json()

    assert len(result) == 1
    assert result[0]["total_amount"] == 3000


def test_categories_zero_total(client, db, auth_headers):
    db.add(
        CategoryStatisticsModel(
            family_id=1,
            category="Продукти",
            total_amount=0,
            period="2026-06"
        )
    )

    db.commit()

    response = client.get(
        "/analytics/categories/2026-06",
        headers=auth_headers()
    )

    assert response.status_code == 200
    assert response.json()[0]["percentage"] == 0


def test_categories_require_authentication(client):
    response = client.get("/analytics/categories/2026-06")

    assert response.status_code == 403