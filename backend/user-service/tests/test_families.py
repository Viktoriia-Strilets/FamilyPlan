
from app import models


def test_head_can_manage_family_and_delete_member(
    client,
    db_session,
    create_family,
):
    """Голова може змінювати назву родини та видаляти її учасників."""
    family = create_family("HeadManageFam", "HM123")

    # Реєструємо голову.
    client.post(
        "/users/register",
        json={
            "username": "HeadGuy",
            "email": "head@hm.com",
            "password": "password123",
            "invite_code": "HM123",
        },
    )

    login_response = client.post(
        "/users/login",
        json={
            "email": "head@hm.com",
            "password": "password123",
        },
    )

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Редагування назви родини.
    update_response = client.put(
        f"/families/{family.id}",
        json={"name": "BrandNewFamilyName"},
        headers=headers,
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == "BrandNewFamilyName"

    # Реєструємо учасника.
    member_response = client.post(
        "/users/register",
        json={
            "username": "SubMember",
            "email": "sub@hm.com",
            "password": "password123",
            "invite_code": "HM123",
        },
    )

    assert member_response.status_code == 201
    member_id = member_response.json()["id"]

    # Голова видаляє учасника.
    delete_member_response = client.delete(
        f"/users/{member_id}",
        headers=headers,
    )

    assert delete_member_response.status_code == 200

    deleted_member = (
        db_session.query(models.UserModel)
        .filter(models.UserModel.id == member_id)
        .first()
    )

    assert deleted_member is None

    # Голова видаляє родину.
    delete_family_response = client.delete(
        f"/families/{family.id}",
        headers=headers,
    )

    assert delete_family_response.status_code == 200
