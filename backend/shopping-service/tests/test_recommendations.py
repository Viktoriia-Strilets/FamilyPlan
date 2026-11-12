
def test_recommendations_empty_history(client, family_headers):
    """Якщо історія покупок порожня, система має повернути базову пораду."""
    response = client.get("/recommendations", headers=family_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["suggested_name"] == "Молоко"
    assert "Порада від системи" in data[0]["title"]


def test_recommendations_based_on_purchase_history(client, family_headers):
    """Система має рекомендувати товари, які родина купувала найчастіше."""
    # Створюємо та купуємо товар кілька разів
    for _ in range(3):
        item = client.post(
            "/items",
            headers=family_headers,
            json={"name": "Кава", "category": "Напої"}
        ).json()
        
        client.patch(
            f"/items/{item['id']}/buy",
            headers=family_headers,
            json={"actual_price": 150}
        )

    # Створюємо інший товар і купуємо 1 раз
    item_other = client.post(
        "/items",
        headers=family_headers,
        json={"name": "Чай", "category": "Напої"}
    ).json()
    client.patch(
        f"/items/{item_other['id']}/buy",
        headers=family_headers,
        json={"actual_price": 50}
    )

    response = client.get("/recommendations", headers=family_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Кава повинна бути на першому місці через більшу кількість покупок
    assert len(data) > 0
    assert data[0]["suggested_name"] == "Кава"
    assert "Часта покупка: Кава" in data[0]["title"]


def test_recommendations_require_authentication(client):
    """Ендпоінт рекомендацій вимагає валідний JWT-токен."""
    response = client.get("/recommendations")
    assert response.status_code == 403