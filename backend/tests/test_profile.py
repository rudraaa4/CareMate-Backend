from tests.conftest import register_and_login


def test_profile_exists_automatically_after_registration(client):
    headers = register_and_login(client)

    response = client.get("/api/v1/profile", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] is None
    assert body["date_of_birth"] is None
    assert body["phone"] is None


def test_profile_requires_auth(client):
    response = client.get("/api/v1/profile")

    assert response.status_code == 401


def test_update_profile_sets_fields(client):
    headers = register_and_login(client)

    response = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={"full_name": "Asha Rao", "phone": "9876543210", "date_of_birth": "1990-05-20"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Asha Rao"
    assert body["phone"] == "9876543210"
    assert body["date_of_birth"] == "1990-05-20"


def test_partial_update_leaves_other_fields_untouched(client):
    headers = register_and_login(client)
    client.patch("/api/v1/profile", headers=headers, json={"full_name": "Asha Rao", "phone": "111"})

    response = client.patch("/api/v1/profile", headers=headers, json={"phone": "222"})

    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Asha Rao"  # untouched by the second PATCH
    assert body["phone"] == "222"


def test_each_user_only_ever_sees_their_own_profile(client):
    headers_a = register_and_login(client, email="a@example.com")
    headers_b = register_and_login(client, email="b@example.com")

    client.patch("/api/v1/profile", headers=headers_a, json={"full_name": "User A"})
    client.patch("/api/v1/profile", headers=headers_b, json={"full_name": "User B"})

    response_a = client.get("/api/v1/profile", headers=headers_a)
    response_b = client.get("/api/v1/profile", headers=headers_b)

    assert response_a.json()["full_name"] == "User A"
    assert response_b.json()["full_name"] == "User B"
