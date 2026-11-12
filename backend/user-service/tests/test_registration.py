
def test_register_first_user_as_head(client, create_family):
    """Перший користувач родини автоматично стає головою."""
    create_family("AlphaFamily", "ALPHA111")

    response = client.post(
        "/users/register",
        json={
            "username": "BossUser",
            "email": "boss@family.com",
            "password": "securepassword123",
            "invite_code": "ALPHA111",
        },
    )

    assert response.status_code == 201

    login_response = client.post(
        "/users/login",
        json={
            "email": "boss@family.com",
            "password": "securepassword123",
        },
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert data["role"] == "head"
    assert "access_token" in data


def test_register_second_user_as_member(client, create_family):
    """Другий користувач родини отримує роль member."""
    create_family("BetaFamily", "BETA222")

    first_response = client.post(
        "/users/register",
        json={
            "username": "HeadUser",
            "email": "head@beta.com",
            "password": "password123",
            "invite_code": "BETA222",
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/users/register",
        json={
            "username": "ChildUser",
            "email": "child@beta.com",
            "password": "password123",
            "invite_code": "BETA222",
        },
    )

    assert second_response.status_code == 201

    login_response = client.post(
        "/users/login",
        json={
            "email": "child@beta.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200
    assert login_response.json()["role"] == "member"
