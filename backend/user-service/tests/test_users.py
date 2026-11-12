
from app import models


def test_head_can_promote_member_and_demote_self(
    client,
    db_session,
    create_family,
):
    """Голова може призначити іншого учасника головою, а потім змінити власну роль."""
    create_family("RolesFam", "ROLE123")

    client.post(
        "/users/register",
        json={
            "username": "Head1",
            "email": "h1@role.com",
            "password": "password123",
            "invite_code": "ROLE123",
        },
    )

    head_login = client.post(
        "/users/login",
        json={
            "email": "h1@role.com",
            "password": "password123",
        },
    )

    head_token = head_login.json()["access_token"]
    head_id = head_login.json()["user_id"]

    client.post(
        "/users/register",
        json={
            "username": "MemberX",
            "email": "m@role.com",
            "password": "password123",
            "invite_code": "ROLE123",
        },
    )

    member = (
        db_session.query(models.UserModel)
        .filter(models.UserModel.email == "m@role.com")
        .first()
    )

    headers = {"Authorization": f"Bearer {head_token}"}

    # Підвищуємо учасника до голови.
    promote_response = client.put(
        f"/users/{member.id}",
        json={"role": "head"},
        headers=headers,
    )

    assert promote_response.status_code == 200
    assert promote_response.json()["role"] == "head"

    # Авторизуємося повторно, щоб отримати актуальний токен.
    fresh_login = client.post(
        "/users/login",
        json={
            "email": "h1@role.com",
            "password": "password123",
        },
    )

    fresh_token = fresh_login.json()["access_token"]

    # Тепер у родині є інший голова, тому першого можна понизити.
    demote_response = client.put(
        f"/users/{head_id}",
        json={"role": "member"},
        headers={"Authorization": f"Bearer {fresh_token}"},
    )

    assert demote_response.status_code == 200
    assert demote_response.json()["role"] == "member"


def test_new_head_is_assigned_when_previous_head_is_deleted(
    client,
    db_session,
    create_family,
    create_admin,
):
    """Якщо видалити голову, іншому учаснику автоматично призначається ця роль."""
    family = create_family("DeleteHeadFam", "DH123")

    client.post(
        "/users/register",
        json={
            "username": "MainHead",
            "email": "mh@dh.com",
            "password": "password123",
            "invite_code": "DH123",
        },
    )

    client.post(
        "/users/register",
        json={
            "username": "SomeMember",
            "email": "sm@dh.com",
            "password": "password123",
            "invite_code": "DH123",
        },
    )

    head = (
        db_session.query(models.UserModel)
        .filter(models.UserModel.email == "mh@dh.com")
        .first()
    )

    # Створюємо адміністратора.
    create_admin(email="admin@familyplan.com", password="pass")

    admin_login = client.post(
        "/users/login",
        json={
            "email": "admin@familyplan.com",
            "password": "pass",
        },
    )

    admin_token = admin_login.json()["access_token"]

    # Адміністратор видаляє голову.
    delete_response = client.delete(
        f"/users/{head.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert delete_response.status_code == 200

    # Перевіряємо призначення нового голови.
    new_head = (
        db_session.query(models.UserModel)
        .filter(
            models.UserModel.family_id == family.id,
            models.UserModel.role == "head",
        )
        .first()
    )

    assert new_head is not None
    assert new_head.email == "sm@dh.com"
