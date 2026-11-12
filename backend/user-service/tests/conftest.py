
import os

os.environ.setdefault(
    "SECRET_KEY",
    "test-secret-key-for-pytest-only"
)

os.environ.setdefault("SESSION_SECRET", "test-session-secret-for-pytest-only")

os.environ.setdefault("ALGORITHM", "HS256")

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app, get_password_hash
from app.database import Base, get_db
from app import models


# Окрема SQLite-база в пам'яті для тестів.
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    """Створює чисту базу перед кожним тестом."""
    Base.metadata.create_all(bind=engine)

    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Надає тесту окрему SQLAlchemy-сесію."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def db(db_session):
    return db_session

@pytest.fixture
def client():
    """Надає HTTP-клієнт FastAPI."""
    return TestClient(app)


@pytest.fixture
def create_family(db_session):
    """Фабрика для створення тестових родин."""

    def _create_family(
        name="TestFamily",
        invite_code="TEST123",
    ):
        family = models.FamilyModel(
            name=name,
            invite_code=invite_code,
        )
        db_session.add(family)
        db_session.commit()
        db_session.refresh(family)
        return family

    return _create_family


@pytest.fixture
def create_admin(db_session):
    """Фабрика для створення системного адміністратора."""

    def _create_admin(
        email="admin@test.com",
        password="adminpassword123",
    ):
        admin = models.UserModel(
            username="TestAdmin",
            email=email,
            password_hash=get_password_hash(password),
            role="admin",
            family_id=None,
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
        return admin

    return _create_admin


@pytest.fixture
def test_user(db_session):
    """Створює звичайного тестового користувача."""

    user = models.UserModel(
        username="TestUser",
        email="test.user@example.com",
        password_hash=get_password_hash("testpassword123"),
        role="member",
        family_id=None,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def second_test_user(db_session):
    """Створює другого тестового користувача."""

    user = models.UserModel(
        username="SecondTestUser",
        email="second.user@example.com",
        password_hash=get_password_hash("testpassword123"),
        role="member",
        family_id=None,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def linked_google_user(db_session, test_user):
    """Створює користувача з уже прив'язаним Google-акаунтом."""

    oauth_account = models.OAuthAccountModel(
        user_id=test_user.id,
        provider="google",
        provider_user_id="google-user-12345",
        email="google.test@gmail.com",
    )

    db_session.add(oauth_account)
    db_session.commit()
    db_session.refresh(test_user)

    return test_user