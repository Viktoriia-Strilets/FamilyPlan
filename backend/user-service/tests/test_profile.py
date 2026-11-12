
from app import models


def test_member_can_update_self_profile_and_delete_account(
    client,
    db_session,
    create_family,
):
    """Учасник може змінити власний профіль і видалити свій акаунт."""
    create_family("MemberFamily", "MEM123")

    # Реєструємо голову родини.
    client.post(
        "/users/register",
        json={
            "username": "Head",
            "email": "head@mem.com",
            "password": "password123",
            "invite_code": "MEM123",
        },
    )

    # Реєструємо учасника.
    client.post(
        "/users/register",
        json={
            "username": "Member",
            "email": "member@mem.com",
            "password": "password123",
            "invite_code": "MEM123",
        },
    )

    login_response = client.post(
        "/users/login",
        json={
            "email": "member@mem.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    login_data = login_response.json()
    token = login_data["access_token"]
    user_id = login_data["user_id"]

    headers = {"Authorization": f"Bearer {token}"}

    # Редагування власного імені.
    update_response = client.put(
        f"/users/{user_id}",
        json={"username": "UpdatedMember"},
        headers=headers,
    )

    assert update_response.status_code == 200
    assert update_response.json()["username"] == "UpdatedMember"

    # Після редагування отримуємо оновлений токен, якщо він повернувся.
    new_token = update_response.json().get("access_token", token)
    new_headers = {"Authorization": f"Bearer {new_token}"}

    # Видалення власного акаунта.
    delete_response = client.delete(
        f"/users/{user_id}",
        headers=new_headers,
    )

    assert delete_response.status_code == 200

    deleted_user = (
        db_session.query(models.UserModel)
        .filter(models.UserModel.id == user_id)
        .first()
    )

    assert deleted_user is None
