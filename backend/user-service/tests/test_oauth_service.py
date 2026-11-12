
import pytest

from sqlalchemy.exc import IntegrityError

from app.models import OAuthAccountModel
from app.services.oauth_service import (
    get_user_by_oauth_identity,
    link_oauth_account,
)
from unittest.mock import AsyncMock
from fastapi.responses import RedirectResponse
from types import SimpleNamespace

def test_get_user_by_oauth_identity_success(
    db_session,
    test_user
):
    """Знаходить користувача за Google sub."""

    account = OAuthAccountModel(
        user_id=test_user.id,
        provider="google",
        provider_user_id="google-user-123",
        email=test_user.email
    )

    db_session.add(account)
    db_session.commit()

    result = get_user_by_oauth_identity(
        db_session,
        "google",
        "google-user-123"
    )

    assert result is not None
    assert result.id == test_user.id


def test_get_user_by_oauth_identity_not_found(db_session):
    """Повертає None, якщо Google-акаунт не прив'язаний."""

    result = get_user_by_oauth_identity(
        db_session,
        "google",
        "unknown-google-user"
    )

    assert result is None


def test_oauth_identity_is_unique(
    db_session,
    test_user
):
    """Не дозволяє створити два однакові зовнішні акаунти."""

    first = OAuthAccountModel(
        user_id=test_user.id,
        provider="google",
        provider_user_id="google-user-unique",
        email=test_user.email
    )

    second = OAuthAccountModel(
        user_id=test_user.id,
        provider="google",
        provider_user_id="google-user-unique",
        email=test_user.email
    )

    db_session.add(first)
    db_session.commit()

    db_session.add(second)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_same_sub_from_different_providers_is_allowed(
    db_session,
    test_user
):
    """Однаковий provider_user_id у різних провайдерів допустимий."""

    google_account = OAuthAccountModel(
        user_id=test_user.id,
        provider="google",
        provider_user_id="external-123",
        email=test_user.email
    )

    facebook_account = OAuthAccountModel(
        user_id=test_user.id,
        provider="facebook",
        provider_user_id="external-123",
        email=test_user.email
    )

    db_session.add_all([
        google_account,
        facebook_account
    ])

    db_session.commit()

    accounts = (
        db_session.query(OAuthAccountModel)
        .filter(
            OAuthAccountModel.user_id == test_user.id
        )
        .all()
    )

    assert len(accounts) == 2


def test_link_oauth_account_success(
    db_session,
    test_user
):
    """Успішно прив'язує Google до існуючого користувача."""

    result = link_oauth_account(
        db_session,
        user_id=test_user.id,
        provider="google",
        provider_user_id="google-link-123",
        email="google.test@gmail.com"
    )

    assert result is not None
    assert result.user_id == test_user.id
    assert result.provider == "google"
    assert result.provider_user_id == "google-link-123"


def test_link_same_oauth_account_twice(
    db_session,
    test_user
):
    """Не дозволяє повторно прив'язати той самий Google-акаунт."""

    link_oauth_account(
        db_session,
        user_id=test_user.id,
        provider="google",
        provider_user_id="google-link-duplicate",
        email="google.test@gmail.com"
    )

    with pytest.raises((ValueError, IntegrityError)):
        link_oauth_account(
            db_session,
            user_id=test_user.id,
            provider="google",
            provider_user_id="google-link-duplicate",
            email="google.test@gmail.com"
        )

    db_session.rollback()


def test_google_account_cannot_be_linked_to_another_user(
    db_session,
    test_user,
    second_test_user
):
    """Один Google-акаунт не можна прив'язати до двох користувачів."""

    link_oauth_account(
        db_session,
        user_id=test_user.id,
        provider="google",
        provider_user_id="google-shared-123",
        email="google.test@gmail.com"
    )

    with pytest.raises((ValueError, IntegrityError)):
        link_oauth_account(
            db_session,
            user_id=second_test_user.id,
            provider="google",
            provider_user_id="google-shared-123",
            email="google.test@gmail.com"
        )

    db_session.rollback()
