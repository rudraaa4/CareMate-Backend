from tests.conftest import register_and_login


def create_medicine(client, headers, **overrides):
    payload = {"name": "Metformin", "strength": "500mg", "instructions": "after food"}
    payload.update(overrides)
    return client.post("/api/v1/medicines", headers=headers, json=payload)


def test_create_medicine(client):
    headers = register_and_login(client)

    response = create_medicine(client, headers)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Metformin"
    assert body["strength"] == "500mg"
    assert body["active"] is True


def test_medicines_require_auth(client):
    assert client.post("/api/v1/medicines", json={"name": "Metformin"}).status_code == 401
    assert client.get("/api/v1/medicines").status_code == 401


def test_list_medicines_returns_only_active_by_default(client):
    headers = register_and_login(client)
    active_id = create_medicine(client, headers, name="Active Med").json()["id"]
    archived_id = create_medicine(client, headers, name="Archived Med").json()["id"]
    client.delete(f"/api/v1/medicines/{archived_id}", headers=headers)

    response = client.get("/api/v1/medicines", headers=headers)

    ids = [m["id"] for m in response.json()]
    assert active_id in ids
    assert archived_id not in ids

    # but it's still retrievable when explicitly asked for
    response_all = client.get("/api/v1/medicines?include_archived=true", headers=headers)
    ids_all = [m["id"] for m in response_all.json()]
    assert archived_id in ids_all


def test_get_medicine_by_id(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]

    response = client.get(f"/api/v1/medicines/{medicine_id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == medicine_id


def test_update_medicine_partial(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]

    response = client.patch(
        f"/api/v1/medicines/{medicine_id}", headers=headers, json={"instructions": "before food"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["instructions"] == "before food"
    assert body["name"] == "Metformin"  # untouched


def test_archive_medicine_soft_deletes(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]

    response = client.delete(f"/api/v1/medicines/{medicine_id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["active"] is False

    # the row still exists — still fetchable by ID, just no longer "active"
    still_there = client.get(f"/api/v1/medicines/{medicine_id}", headers=headers)
    assert still_there.status_code == 200
    assert still_there.json()["active"] is False


def test_patient_a_cannot_read_patient_bs_medicine(client):
    """The critical security test the spec calls out explicitly."""
    headers_a = register_and_login(client, email="a@example.com")
    headers_b = register_and_login(client, email="b@example.com")
    medicine_id = create_medicine(client, headers_a, name="Patient A's Secret Med").json()["id"]

    response = client.get(f"/api/v1/medicines/{medicine_id}", headers=headers_b)

    assert response.status_code == 404


def test_patient_a_cannot_update_patient_bs_medicine(client):
    headers_a = register_and_login(client, email="a@example.com")
    headers_b = register_and_login(client, email="b@example.com")
    medicine_id = create_medicine(client, headers_a).json()["id"]

    response = client.patch(
        f"/api/v1/medicines/{medicine_id}", headers=headers_b, json={"name": "Hijacked"}
    )

    assert response.status_code == 404
    # and it really wasn't changed
    unchanged = client.get(f"/api/v1/medicines/{medicine_id}", headers=headers_a)
    assert unchanged.json()["name"] != "Hijacked"


def test_patient_a_cannot_archive_patient_bs_medicine(client):
    headers_a = register_and_login(client, email="a@example.com")
    headers_b = register_and_login(client, email="b@example.com")
    medicine_id = create_medicine(client, headers_a).json()["id"]

    response = client.delete(f"/api/v1/medicines/{medicine_id}", headers=headers_b)

    assert response.status_code == 404
    still_active = client.get(f"/api/v1/medicines/{medicine_id}", headers=headers_a)
    assert still_active.json()["active"] is True


def test_patient_bs_medicine_list_never_includes_patient_as(client):
    headers_a = register_and_login(client, email="a@example.com")
    headers_b = register_and_login(client, email="b@example.com")
    create_medicine(client, headers_a, name="Only A's")

    response = client.get("/api/v1/medicines", headers=headers_b)

    assert response.json() == []
