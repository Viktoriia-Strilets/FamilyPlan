
import pytest


@pytest.mark.parametrize(
    "method,url",
    [
        ("GET", "/items"),
        ("GET", "/history"),
        ("GET", "/recommendations"),
        ("GET", "/reminders"),
    ]
)
def test_endpoints_require_authentication(client, method, url):
    """Захищені endpoints не повинні працювати без авторизації."""

    response = client.request(method, url)

    assert response.status_code == 403, (
        f"Endpoint {method} {url} доступний без авторизації. "
        f"Отриманий статус: {response.status_code}"
    )


def test_invalid_token(client):
    """Перевірка відхилення недійсного JWT."""

    response = client.get(
        "/items",
        headers={
            "Authorization": "Bearer invalid_token"
        }
    )

    assert response.status_code == 401


def test_root(client):
    """Перевірка доступності кореневого endpoint."""

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Shopping Service is running"
    }
