import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from jose import jwt

from app.main import app
from app.database import Base, get_db
from app.dependencies import SECRET_KEY, ALGORITHM


SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)

    connection = engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def create_token(
    email="test@example.com",
    family_id=1,
    role="member",
    username="Test User"
):
    payload = {
        "sub": email,
        "family_id": family_id,
        "role": role,
        "username": username
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


@pytest.fixture()
def auth_headers():
    def _auth_headers(
        email="test@example.com",
        family_id=1,
        role="member",
        username="Test User"
    ):
        token = create_token(
            email=email,
            family_id=family_id,
            role=role,
            username=username
        )

        return {
            "Authorization": f"Bearer {token}"
        }

    return _auth_headers