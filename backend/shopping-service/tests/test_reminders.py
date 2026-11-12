from datetime import datetime, timedelta, timezone

def test_reminders_empty(client, family_headers):
    """Якщо немає активних товарів із датами, список нагадувань порожній."""
    response = client.get("/reminders", headers=family_headers)
    
    assert response.status_code == 200
    assert response.json() == []


def test_reminders_for_today_and_overdue(client, family_headers):
    """Система має формувати попередження для прострочених та сьогоднішніх товарів."""
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    past_str = (now - timedelta(days=2)).strftime("%Y-%m-%d")
    future_str = (now + timedelta(days=5)).strftime("%Y-%m-%d")

    # 1. Прострочений товар
    client.post(
        "/items",
        headers=family_headers,
        json={"name": "Старий хліб", "planned_date": f"{past_str}T12:00:00Z"}
    )

    # 2. Товар на сьогодні
    client.post(
        "/items",
        headers=family_headers,
        json={"name": "Свіже молоко", "planned_date": f"{today_str}T12:00:00Z"}
    )

    # 3. Товар у майбутньому (не повинен створювати нагадування)
    client.post(
        "/items",
        headers=family_headers,
        json={"name": "Майбутній сік", "planned_date": f"{future_str}T12:00:00Z"}
    )

    response = client.get("/reminders", headers=family_headers)
    
    assert response.status_code == 200
    reminders = response.json()
    
    # Має бути рівно 2 нагадування (прострочене + сьогоднішнє)
    assert len(reminders) == 2
    
    levels = [r["level"] for r in reminders]
    assert "danger" in levels  # прострочено
    assert "warning" in levels  # сьогодні


def test_reminders_isolation_between_families(
    client,
    family_headers,
    second_family_headers
):
    """Нагадування однієї сім'ї не повинні з'являтися у іншої."""
    past_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    # Перша родина створює прострочений товар
    client.post(
        "/items",
        headers=family_headers,
        json={"name": "Борг першої сім'ї", "planned_date": f"{past_date}T12:00:00Z"}
    )

    # Друга родина робить запит на свої нагадування
    response = client.get("/reminders", headers=second_family_headers)
    
    assert response.status_code == 200
    assert response.json() == []


def test_reminders_require_authentication(client):
    """Ендпоінт нагадувань вимагає валідний JWT-токен."""
    response = client.get("/reminders")
    assert response.status_code == 403