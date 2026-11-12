
import pytest
from fastapi.responses import RedirectResponse
from unittest.mock import AsyncMock

from app.core.oauth import oauth
from types import SimpleNamespace

GOOGLE_USERINFO = {
    "sub": "google-user-12345",
    "email": "google.test@gmail.com",
    "email_verified": True,
    "name": "Google Test User",
}


def mock_google_response(userinfo=None):
    """Підміняє відповідь Google під час тестування."""
    return {
        "userinfo": userinfo or GOOGLE_USERINFO
    }


def test_google_login_redirects_to_google(client, monkeypatch):
    mock_redirect = AsyncMock(
        return_value=RedirectResponse(
            url="https://accounts.google.com/o/oauth2/auth"
        )
    )

    mock_google = SimpleNamespace(
        authorize_redirect=mock_redirect
    )

    monkeypatch.setattr(oauth, "google", mock_google)

    monkeypatch.setenv(
        "GOOGLE_REDIRECT_URI",
        "http://localhost:8000/auth/google/callback"
    )

    response = client.get(
        "/auth/google/login",
        follow_redirects=False
    )

    assert response.status_code in (302, 307)
    mock_redirect.assert_awaited_once()


def test_google_callback_success(
    client,
    monkeypatch,
    linked_google_user
):
    """Успішний callback для вже прив'язаного Google-акаунта."""

    mock_token = AsyncMock(
        return_value=mock_google_response()
    )

    monkeypatch.setattr(
        oauth.google,
        "authorize_access_token",
        mock_token
    )

    response = client.get(
        "/auth/google/callback",
        follow_redirects=False
    )

    assert response.status_code in (302, 307)

    # Перевіряємо, що Google OAuth було викликано.
    mock_token.assert_awaited_once()

    # Перевіряємо перенаправлення на frontend.
    assert response.headers["location"].startswith(
        "http://localhost:5173/oauth/callback"
    )

    # Перевіряємо наявність JWT у URL.
    assert "#access_token=" in response.headers["location"]


@pytest.mark.parametrize(
    "userinfo",
    [
        {
            "email": "test@gmail.com",
            "email_verified": True
        },
        {
            "sub": "google-user-12345",
            "email_verified": True
        },
        {
            "sub": "google-user-12345",
            "email": "test@gmail.com",
            "email_verified": False
        },
        {
            "sub": "google-user-12345",
            "email": "test@gmail.com",
        },
    ]
)
def test_google_callback_invalid_userinfo(
    client,
    monkeypatch,
    userinfo
):
    """Відхиляє профілі без sub, email або підтвердженого email."""

    mock_token = AsyncMock(
        return_value=mock_google_response(userinfo)
    )

    monkeypatch.setattr(
        oauth.google,
        "authorize_access_token",
        mock_token
    )

    response = client.get(
        "/auth/google/callback"
    )

    assert response.status_code == 401


def test_google_callback_google_error(
    client,
    monkeypatch
):
    """Перевіряє обробку помилки під час отримання токена Google."""

    mock_token = AsyncMock(
        side_effect=Exception("Google OAuth error")
    )

    monkeypatch.setattr(
        oauth.google,
        "authorize_access_token",
        mock_token
    )

    response = client.get(
        "/auth/google/callback"
    )

    assert response.status_code >= 400


def test_google_oauth_not_configured(client, monkeypatch):
    """Перевіряє поведінку, якщо Google OAuth не налаштований."""

    monkeypatch.setattr(
        "app.routers.oauth.oauth.google",
        None
    )

    response = client.get("/auth/google/login")

    assert response.status_code == 503
