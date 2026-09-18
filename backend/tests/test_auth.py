from datetime import timedelta

from app.core.security import create_access_token

VALID_PASSWORD = "correct-horse-battery-staple"


def register(client, email="patient@example.com", password=VALID_PASSWORD):
    return client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )


def login(client, email="patient@example.com", password=VALID_PASSWORD):
    # OAuth2PasswordRequestForm expects form-encoded data, not JSON, and
    # names the field "username" even though we're sending an email.
    return client.post(
        "/api/v1/auth/login", data={"username": email, "password": password}
    )


def test_register_creates_user_without_leaking_password_hash(client):
    response = register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "patient@example.com"
    assert body["role"] == "patient"
    assert body["is_active"] is True
    assert "password" not in body
    assert "password_hash" not in body


def test_register_rejects_duplicate_email(client):
    register(client)
    response = register(client)

    assert response.status_code == 409


def test_login_returns_jwt_on_correct_credentials(client):
    register(client)
    response = login(client)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 0


def test_login_rejects_wrong_password(client):
    register(client)
    response = login(client, password="totally-wrong-password")

    assert response.status_code == 401


def test_login_rejects_unknown_email(client):
    response = login(client, email="nobody@example.com")

    assert response.status_code == 401


def test_me_returns_current_user_with_valid_token(client):
    register(client)
    token = login(client).json()["access_token"]

    response = client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["email"] == "patient@example.com"


def test_me_rejects_missing_token(client):
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401


def test_me_rejects_garbage_token(client):
    response = client.get(
        "/api/v1/users/me", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert response.status_code == 401


def test_me_rejects_expired_token(client):
    register(client)
    expired_token = create_access_token(
        data={"sub": "1"}, expires_delta=timedelta(seconds=-1)
    )

    response = client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {expired_token}"}
    )

    assert response.status_code == 401
