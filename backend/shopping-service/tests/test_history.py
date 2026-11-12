# =====================================================
# 5. ІСТОРІЯ ПОКУПОК
# =====================================================

def test_get_purchase_history(
    client,
    family_headers
):
    # Додаємо перший товар
    first = client.post(
        "/items",
        headers=family_headers,
        json={
            "name": "Молоко"
        }
    ).json()

    # Додаємо другий товар
    second = client.post(
        "/items",
        headers=family_headers,
        json={
            "name": "Хліб"
        }
    ).json()

    # Купуємо лише перший товар
    client.patch(
        f"/items/{first['id']}/buy",
        headers=family_headers,
        json={
            "actual_price": 50
        }
    )

    response = client.get(
        "/history",
        headers=family_headers
    )

    assert response.status_code == 200

    history = response.json()

    assert len(history) == 1
    assert history[0]["name"] == "Молоко"
    assert history[0]["is_purchased"] is True


def test_purchase_history_empty(
    client,
    family_headers
):
    response = client.get(
        "/history",
        headers=family_headers
    )

    assert response.status_code == 200
    assert response.json() == []

def test_family_cannot_see_other_family_history(
    client,
    family_headers,
    second_family_headers
):
    create_response = client.post(
        "/items",
        headers=family_headers,
        json={
            "name": "Молоко"
        }
    )

    item_id = create_response.json()["id"]

    client.patch(
        f"/items/{item_id}/buy",
        headers=family_headers,
        json={
            "actual_price": 50
        }
    )

    response = client.get(
        "/history",
        headers=second_family_headers
    )

    assert response.status_code == 200
    assert response.json() == []