
from datetime import datetime, timedelta

from app import models


def test_admin_can_find_and_delete_inactive_family(
    client,
    db_session,
    create_admin,
):
    """Адміністратор бачить неактивні родини та може їх видаляти."""
    create_admin(
        email="admin@familyplan.com",
        password="SuperSecretPassword123",
    )

    # Створюємо родину, неактивну понад 180 днів.
    old_date = datetime.utcnow() - timedelta(days=200)

    inactive_family = models.FamilyModel(
        name="InactiveFamilyUnique",
        invite_code="INACT1",
        created_at=old_date,
        last_activity_at=old_date,
    )

    db_session.add(inactive_family)
    db_session.commit()
    db_session.refresh(inactive_family)

    family_id = inactive_family.id

    # Авторизуємо адміністратора.
    login_response = client.post(
        "/users/login",
        json={
            "email": "admin@familyplan.com",
            "password": "SuperSecretPassword123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Отримуємо список родин.
    response = client.get(
        "/admin/families",
        headers=headers,
    )

    assert response.status_code == 200

    families = response.json()

    target_family = next(
        (
            family
            for family in families
            if family["name"] == "InactiveFamilyUnique"
        ),
        None,
    )

    assert target_family is not None
    assert target_family["is_inactive"] is True
    assert target_family["can_be_deleted"] is True
    assert "head_email" in target_family

    # Видаляємо неактивну родину.
    delete_response = client.delete(
        f"/admin/families/{family_id}",
        headers=headers,
    )

    assert delete_response.status_code == 200

    deleted_family = (
        db_session.query(models.FamilyModel)
        .filter(models.FamilyModel.id == family_id)
        .first()
    )

    assert deleted_family is None
