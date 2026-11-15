import os

# Must be set BEFORE the app is imported.
os.environ["SECRET_KEY"] = "test-secret-key-only-for-running-tests-0123456789"
os.environ["DATABASE_URL"] = "sqlite:///./test_market.db"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def make_user(client, email="alice@example.com", username="alice", password="Passw0rd123"):
    r = client.post(
        "/auth/register", json={"email": email, "username": username, "password": password}
    )
    assert r.status_code == 201, r.text
    return r.json()


def auth_headers(client, identifier="alice", password="Passw0rd123"):
    r = client.post("/auth/login", data={"username": identifier, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
