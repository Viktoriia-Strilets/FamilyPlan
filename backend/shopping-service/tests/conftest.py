
import os
from datetime import datetime, timedelta, timezone

# Встановлюємо тестові налаштування до імпорту app.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test_secret_key_for_shopping_service"

os.environ.setdefault(
    "ENABLE_EMAIL_REMINDERS",
    "false"
)

import pytest

from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app import models


# Тестова SQLite БД у пам'яті
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


@pytest.fixture
def db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    connection = test_engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(
        bind=connection,
        join_transaction_mode="create_savepoint"
    )

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def mock_budget_service(monkeypatch):
    async def fake_send_purchase_to_budget(**kwargs):
        return {
            "message": "Покупку передано до Budget Service"
        }

    async def fake_complete_planned_expense(**kwargs):
        return {
            "message": "Заплановану витрату завершено"
        }

    monkeypatch.setattr(
        "app.routers.items.send_purchase_to_budget",
        fake_send_purchase_to_budget
    )

    monkeypatch.setattr(
        "app.routers.items.complete_planned_expense",
        fake_complete_planned_expense
    )

@pytest.fixture
def token_headers():
    def create_headers(
        family_id=1,
        email="user1@example.com",
        username="Тестовий користувач",
        role="member"
    ):
        payload = {
            "sub": email,
            "username": username,
            "family_id": family_id,
            "role": role,
            "exp": (
                datetime.now(timezone.utc)
                + timedelta(hours=1)
            )
        }

        token = jwt.encode(
            payload,
            os.environ["SECRET_KEY"],
            algorithm="HS256"
        )

        return {
            "Authorization": f"Bearer {token}"
        }

    return create_headers


@pytest.fixture
def family_headers(token_headers):
    return token_headers(family_id=1)


@pytest.fixture
def second_family_headers(token_headers):
    return token_headers(
        family_id=2,
        email="user2@example.com"
    )
