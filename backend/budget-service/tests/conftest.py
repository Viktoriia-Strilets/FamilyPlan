
import os
from datetime import datetime

# Змінні середовища задаємо до імпорту app.auth
os.environ.setdefault(
    "SECRET_KEY",
    "test-secret-key-for-pytest-only"
)

os.environ.setdefault("ALGORITHM", "HS256")

import pytest

from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

import app.main as main_module
from app.database import Base, get_db
from app import models


SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"


# Окрема SQLite БД для тестів
SQLALCHEMY_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(db_session, monkeypatch):
    # Підміняємо PostgreSQL engine на SQLite
    monkeypatch.setattr(
        main_module,
        "engine",
        test_engine
    )

    def override_get_db():
        yield db_session

    main_module.app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(main_module.app) as test_client:
            yield test_client
    finally:
        main_module.app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """
    Створює JWT для тестового користувача.

    get_current_user очікує:
    sub, role, family_id, username.
    """

    def _create_headers(
        email,
        family_id,
        role="member",
        username=None
    ):
        payload = {
            "sub": email,
            "role": role,
            "family_id": family_id,
            "username": username or email.split("@")[0],
        }

        token = jwt.encode(
            payload,
            SECRET_KEY,
            algorithm=ALGORITHM
        )

        return {
            "Authorization": f"Bearer {token}"
        }

    return _create_headers


@pytest.fixture
def create_budget(client):
    """
    Створює бюджет через POST /budgets.
    """

    def _create_budget(
        headers,
        amount=10000,
        start="2026-06-01T00:00:00",
        end="2026-06-30T23:59:59",
        currency="UAH"
    ):
        payload = {
            "total_planned_budget": amount,
            "currency": currency,
            "start_date": start,
            "end_date": end,
        }

        response = client.post(
            "/budgets",
            json=payload,
            headers=headers
        )

        assert response.status_code == 200, (
            "Не вдалося створити тестовий бюджет. "
            f"Status: {response.status_code}; "
            f"Response: {response.text}"
        )

        return response.json()

    return _create_budget


@pytest.fixture
def create_expense(client):
    """
    Створює фактичну витрату або заплановану витрату
    через POST /budgets/expenses.
    """

    def _create_expense(
        headers,
        title,
        amount,
        date="2026-06-15T12:00:00",
        is_planned=0,
        category="Покупки"
    ):
        payload = {
            "title": title,
            "amount": amount,
            "category": category,
            "is_planned": int(is_planned),
            "date": date,
        }

        response = client.post(
            "/budgets/expenses",
            json=payload,
            headers=headers
        )

        assert response.status_code == 200, (
            "Не вдалося створити тестову витрату. "
            f"Status: {response.status_code}; "
            f"Response: {response.text}"
        )

        return response.json()

    return _create_expense
