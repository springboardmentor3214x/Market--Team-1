from datetime import timedelta

from app.security import create_access_token
from tests.conftest import auth_headers, make_user


def test_register_success_and_no_password_leak(client):
    user = make_user(client)
    assert user["email"] == "alice@example.com"
    assert "password" not in user and "hashed_password" not in user


def test_register_duplicate_email_and_username(client):
    make_user(client)
    r = client.post(
        "/auth/register",
        json={"email": "ALICE@example.com", "username": "other", "password": "Passw0rd123"},
    )
    assert r.status_code == 409
    r = client.post(
        "/auth/register",
        json={"email": "new@example.com", "username": "Alice", "password": "Passw0rd123"},
    )
    assert r.status_code == 409


def test_register_weak_password_rejected(client):
    r = client.post(
        "/auth/register",
        json={"email": "a@example.com", "username": "abc", "password": "onlyletters"},
    )
    assert r.status_code == 422


def test_login_with_email_and_username(client):
    make_user(client)
    assert client.post(
        "/auth/login", data={"username": "alice@example.com", "password": "Passw0rd123"}
    ).status_code == 200
    assert client.post(
        "/auth/login", data={"username": "alice", "password": "Passw0rd123"}
    ).status_code == 200


def test_login_json(client):
    make_user(client)
    r = client.post(
        "/auth/login-json", json={"identifier": "alice", "password": "Passw0rd123"}
    )
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"


def test_login_wrong_password_and_unknown_user(client):
    make_user(client)
    assert client.post(
        "/auth/login", data={"username": "alice", "password": "WrongPass1"}
    ).status_code == 401
    assert client.post(
        "/auth/login", data={"username": "ghost", "password": "Passw0rd123"}
    ).status_code == 401


def test_me_requires_valid_token(client):
    make_user(client)
    assert client.get("/auth/me").status_code == 401
    headers = auth_headers(client)
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["username"] == "alice"


def test_tampered_token_rejected(client):
    make_user(client)
    token = auth_headers(client)["Authorization"].split()[1]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}tampered"})
    assert r.status_code == 401


def test_expired_token_rejected(client):
    user = make_user(client)
    token = create_access_token(str(user["id"]), timedelta(minutes=-5))
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_token_for_deleted_user_rejected(client):
    token = create_access_token("9999")
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
