def test_unauthorized_user_cannot_get_families(client):
    response = client.get("/families")

    assert response.status_code == 401

def test_member_can_only_get_own_family(
    client,
    create_family,
):
    family1 = create_family("FamilyOne", "ONE123")
    create_family("FamilyTwo", "TWO123")

    client.post(
        "/users/register",
        json={
            "username": "MemberOne",
            "email": "one@test.com",
            "password": "password123",
            "invite_code": "ONE123",
        },
    )

    login = client.post(
        "/users/login",
        json={
            "email": "one@test.com",
            "password": "password123",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    response = client.get(
        "/families",
        headers=headers,
    )

    assert response.status_code == 200

    families = response.json()

    assert len(families) == 1
    assert families[0]["id"] == family1.id

def test_user_cannot_update_profile_of_another_family(
    client,
    create_family,
):
    create_family("FirstFamily", "FIRST123")
    create_family("SecondFamily", "SECOND123")

    # Реєструємо користувача першої родини.
    client.post(
        "/users/register",
        json={
            "username": "FirstHead",
            "email": "first@test.com",
            "password": "password123",
            "invite_code": "FIRST123",
        },
    )

    # Реєструємо користувача другої родини.
    second_user = client.post(
        "/users/register",
        json={
            "username": "SecondHead",
            "email": "second@test.com",
            "password": "password123",
            "invite_code": "SECOND123",
        },
    ).json()

    login = client.post(
        "/users/login",
        json={
            "email": "first@test.com",
            "password": "password123",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    response = client.put(
        f"/users/{second_user['id']}",
        json={"username": "HackedName"},
        headers=headers,
    )

    assert response.status_code == 403

def test_member_cannot_promote_self_to_admin(
    client,
    create_family,
):
    create_family("RoleFamily", "ROLE123")

    client.post(
        "/users/register",
        json={
            "username": "Head",
            "email": "head-role@test.com",
            "password": "password123",
            "invite_code": "ROLE123",
        },
    )

    member = client.post(
        "/users/register",
        json={
            "username": "Member",
            "email": "member-role@test.com",
            "password": "password123",
            "invite_code": "ROLE123",
        },
    ).json()

    login = client.post(
        "/users/login",
        json={
            "email": "member-role@test.com",
            "password": "password123",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    response = client.put(
        f"/users/{member['id']}",
        json={"role": "admin"},
        headers=headers,
    )

    assert response.status_code == 403

def test_registration_with_invalid_invite_code(client):
    response = client.post(
        "/users/register",
        json={
            "username": "NewUser",
            "email": "new-user@test.com",
            "password": "password123",
            "invite_code": "WRONG123",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Родину з таким кодом запрошення не знайдено"
    )