# =====================================================
# 1. ОТРИМАННЯ СПИСКУ ПОКУПОК
# =====================================================

def test_get_items_empty(client, family_headers):
    response = client.get(
        "/items",
        headers=family_headers
    )

    assert response.status_code == 200
    assert response.json() == []


def test_get_items_returns_family_items(
    client,
    family_headers
):
    # Створюємо товар
    create_response = client.post(
        "/items",
        headers=family_headers,
        json={
            "name": "Молоко",
            "quantity": 2,
            "category": "Продукти",
            "estimated_price": 50.00
        }
    )

    assert create_response.status_code == 201

    # Отримуємо список
    response = client.get(
        "/items",
        headers=family_headers
    )

    assert response.status_code == 200

    items = response.json()

    assert len(items) == 1
    assert items[0]["name"] == "Молоко"
    assert items[0]["quantity"] == 2
    assert items[0]["category"] == "Продукти"


# =====================================================
# 2. ДОДАВАННЯ ТОВАРУ
# =====================================================

def test_create_item_success(client, family_headers):
    response = client.post(
        "/items",
        headers=family_headers,
        json={
            "name": "Хліб",
            "quantity": 3,
            "category": "Продукти",
            "estimated_price": 35.50
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] is not None
    assert data["name"] == "Хліб"
    assert data["family_id"] == 1
    assert data["created_by"] == "Тестовий користувач"
    assert data["quantity"] == 3
    assert data["category"] == "Продукти"
    assert float(data["estimated_price"]) == 35.50
    assert data["actual_price"] is None
    assert data["is_purchased"] is False
    assert data["purchased_at"] is None


def test_create_item_without_optional_fields(
    client,
    family_headers
):
    response = client.post(
        "/items",
        headers=family_headers,
        json={
            "name": "Яблука"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Яблука"
    assert data["quantity"] == 1
    assert data["category"] is None
    assert data["estimated_price"] is None
    assert data["planned_date"] is None


def test_create_item_invalid_quantity(
    client,
    family_headers
):
    response = client.post(
        "/items",
        headers=family_headers,
        json={
            "name": "Молоко",
            "quantity": 0
        }
    )

    assert response.status_code == 422


def test_create_item_negative_estimated_price(
    client,
    family_headers
):
    response = client.post(
        "/items",
        headers=family_headers,
        json={
            "name": "Молоко",
            "estimated_price": -50
        }
    )

    assert response.status_code == 422


def test_create_item_without_name(
    client,
    family_headers
):
    response = client.post(
        "/items",
        headers=family_headers,
        json={
            "quantity": 1
        }
    )

    assert response.status_code == 422


# =====================================================
# 3. РЕДАГУВАННЯ ТОВАРУ
# =====================================================

def test_update_item_name(client, family_headers):
    create_response = client.post(
        "/items",
        headers=family_headers,
        json={
            "name": "Молоко"
        }
    )

    item_id = create_response.json()["id"]

    response = client.put(
        f"/items/{item_id}",
        headers=family_headers,
        json={
            "name": "Молоко 2.5%"
        }
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Молоко 2.5%"


def test_update_item_quantity_and_price(
    client,
    family_headers
):
    create_response = client.post(
        "/items",
        headers=family_headers,
        json={
            "name": "Яблука",
            "quantity": 1,
            "estimated_price": 40
        }
    )

    item_id = create_response.json()["id"]

    response = client.put(
        f"/items/{item_id}",
        headers=family_headers,
        json={
            "quantity": 3,
            "estimated_price": 120
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["quantity"] == 3
    assert float(data["estimated_price"]) == 120.00


def test_update_item_not_found(client, family_headers):
    response = client.put(
        "/items/999",
        headers=family_headers,
        json={
            "name": "Новий товар"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Товар не знайдено"


# =====================================================
# 4. ПОЗНАЧЕННЯ ТОВАРУ ЯК ПРИДБАНОГО
# =====================================================

def test_mark_item_as_purchased(
    client,
    family_headers
):
    create_response = client.post(
        "/items",
        headers=family_headers,
        json={
            "name": "Молоко",
            "estimated_price": 50
        }
    )

    item_id = create_response.json()["id"]

    response = client.patch(
        f"/items/{item_id}/buy",
        headers=family_headers,
        json={
            "actual_price": 54.50
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["is_purchased"] is True
    assert float(data["actual_price"]) == 54.50
    assert data["purchased_at"] is not None


def test_mark_item_as_purchased_without_actual_price(
    client,
    family_headers
):
    create_response = client.post(
        "/items",
        headers=family_headers,
        json={
            "name": "Хліб"
        }
    )

    item_id = create_response.json()["id"]

    response = client.patch(
        f"/items/{item_id}/buy",
        headers=family_headers,
        json={}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["is_purchased"] is True
    assert data["actual_price"] is None


def test_mark_item_as_purchased_negative_price(
    client,
    family_headers
):
    create_response = client.post(
        "/items",
        headers=family_headers,
        json={
            "name": "Хліб"
        }
    )

    item_id = create_response.json()["id"]

    response = client.patch(
        f"/items/{item_id}/buy",
        headers=family_headers,
        json={
            "actual_price": -10
        }
    )

    assert response.status_code == 422


def test_mark_already_purchased_item(
    client,
    family_headers
):
    create_response = client.post(
        "/items",
        headers=family_headers,
        json={
            "name": "Хліб"
        }
    )

    item_id = create_response.json()["id"]

    client.patch(
        f"/items/{item_id}/buy",
        headers=family_headers,
        json={
            "actual_price": 30
        }
    )

    response = client.patch(
        f"/items/{item_id}/buy",
        headers=family_headers,
        json={
            "actual_price": 35
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Товар уже позначений як придбаний"
    )


def test_mark_item_not_found(client, family_headers):
    response = client.patch(
        "/items/999/buy",
        headers=family_headers,
        json={}
    )

    assert response.status_code == 404

def test_delete_item(client, family_headers):
    create_response = client.post(
        "/items",
        headers=family_headers,
        json={
            "name": "Молоко"
        }
    )

    item_id = create_response.json()["id"]

    response = client.delete(
        f"/items/{item_id}",
        headers=family_headers
    )

    assert response.status_code == 200
    assert "успішно видалено" in response.json()["message"]

    # Перевіряємо, що товар справді видалений
    items_response = client.get(
        "/items",
        headers=family_headers
    )

    assert items_response.json() == []


def test_delete_item_not_found(client, family_headers):
    response = client.delete(
        "/items/999",
        headers=family_headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Товар не знайдено"


# =====================================================
# 7. ІЗОЛЯЦІЯ ДАНИХ РОДИН
# =====================================================

def test_different_families_see_different_items(
    client,
    family_headers,
    second_family_headers
):
    # Перша родина додає молоко
    client.post(
        "/items",
        headers=family_headers,
        json={
            "name": "Молоко"
        }
    )

    # Друга родина додає хліб
    client.post(
        "/items",
        headers=second_family_headers,
        json={
            "name": "Хліб"
        }
    )

    first_response = client.get(
        "/items",
        headers=family_headers
    )

    second_response = client.get(
        "/items",
        headers=second_family_headers
    )

    assert len(first_response.json()) == 1
    assert first_response.json()[0]["name"] == "Молоко"

    assert len(second_response.json()) == 1
    assert second_response.json()[0]["name"] == "Хліб"


def test_family_cannot_update_other_family_item(
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

    response = client.put(
        f"/items/{item_id}",
        headers=second_family_headers,
        json={
            "name": "Чужий товар"
        }
    )

    assert response.status_code == 404


def test_family_cannot_delete_other_family_item(
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

    response = client.delete(
        f"/items/{item_id}",
        headers=second_family_headers
    )

    assert response.status_code == 404


def test_family_cannot_purchase_other_family_item(
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

    response = client.patch(
        f"/items/{item_id}/buy",
        headers=second_family_headers,
        json={
            "actual_price": 50
        }
    )

    assert response.status_code == 404

def test_two_members_of_same_family_share_shopping_list(
    client,
    token_headers,
):
    first_member = token_headers(
        family_id=10,
        email="first-member@test.com",
        username="Перший учасник",
    )

    second_member = token_headers(
        family_id=10,
        email="second-member@test.com",
        username="Другий учасник",
    )

    # Перший учасник створює товар.
    create_response = client.post(
        "/items",
        headers=first_member,
        json={
            "name": "Молоко",
            "quantity": 2,
        },
    )

    assert create_response.status_code == 201

    item_id = create_response.json()["id"]

    # Другий учасник бачить цей товар.
    list_response = client.get(
        "/items",
        headers=second_member,
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["name"] == "Молоко"

    # Другий учасник редагує товар.
    update_response = client.put(
        f"/items/{item_id}",
        headers=second_member,
        json={
            "name": "Молоко 2.5%",
            "quantity": 3,
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Молоко 2.5%"
    assert update_response.json()["quantity"] == 3

    # Перший учасник бачить оновлені дані.
    final_response = client.get(
        "/items",
        headers=first_member,
    )

    assert final_response.status_code == 200
    assert final_response.json()[0]["name"] == "Молоко 2.5%"