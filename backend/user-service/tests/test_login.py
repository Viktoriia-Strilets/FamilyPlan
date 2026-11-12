
def test_login_with_wrong_password(client, db):
    from app.models import FamilyModel

    db.add(
        FamilyModel(
            name="LoginFamily",
            invite_code="LOGIN123"
        )
    )
    db.commit()

    client.post(
        "/users/register",
        json={
            "username": "TestUser",
            "email": "test@login.com",
            "password": "password123",
            "invite_code": "LOGIN123"
        }
    )

    response = client.post(
        "/users/login",
        json={
            "email": "test@login.com",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401


def test_login_with_unknown_email(client):
    response = client.post(
        "/users/login",
        json={
            "email": "unknown@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 401
