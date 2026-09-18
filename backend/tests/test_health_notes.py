from app.core.timezone import local_now
from tests.conftest import register_and_login
from tests.test_medicines import create_medicine


def create_note(client, headers, **overrides):
    payload = {"text": "Felt a bit nauseous after the evening dose"}
    payload.update(overrides)
    return client.post("/api/v1/health-notes", headers=headers, json=payload)


def test_create_note_defaults_recorded_at_to_now(client):
    headers = register_and_login(client)
    before = local_now()

    response = create_note(client, headers)

    assert response.status_code == 201
    body = response.json()
    assert body["text"] == "Felt a bit nauseous after the evening dose"
    assert body["medicine_id"] is None
    recorded_at = body["recorded_at"]
    assert recorded_at is not None
    # sanity: recorded within a few seconds of "now", not left null/epoch
    from datetime import datetime

    assert abs((datetime.fromisoformat(recorded_at) - before).total_seconds()) < 5


def test_create_note_with_explicit_recorded_at(client):
    headers = register_and_login(client)

    response = create_note(client, headers, recorded_at="2026-01-01T09:00:00+05:30")

    assert response.status_code == 201
    assert response.json()["recorded_at"] == "2026-01-01T09:00:00+05:30"


def test_create_note_with_medicine_association(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]

    response = create_note(client, headers, medicine_id=medicine_id)

    assert response.status_code == 201
    assert response.json()["medicine_id"] == medicine_id


def test_create_note_rejects_medicine_not_owned(client):
    headers_a = register_and_login(client, email="a@example.com")
    headers_b = register_and_login(client, email="b@example.com")
    medicine_id = create_medicine(client, headers_a).json()["id"]

    response = create_note(client, headers_b, medicine_id=medicine_id)

    assert response.status_code == 400


def test_list_notes_ordered_by_recorded_at_desc(client):
    headers = register_and_login(client)
    create_note(client, headers, text="Earlier note", recorded_at="2026-01-01T08:00:00+05:30")
    create_note(client, headers, text="Later note", recorded_at="2026-01-02T08:00:00+05:30")

    response = client.get("/api/v1/health-notes", headers=headers)

    texts = [note["text"] for note in response.json()]
    assert texts == ["Later note", "Earlier note"]


def test_get_note_by_id(client):
    headers = register_and_login(client)
    note_id = create_note(client, headers).json()["id"]

    response = client.get(f"/api/v1/health-notes/{note_id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == note_id


def test_update_note_text(client):
    headers = register_and_login(client)
    note_id = create_note(client, headers).json()["id"]

    response = client.patch(
        f"/api/v1/health-notes/{note_id}", headers=headers, json={"text": "Updated text"}
    )

    assert response.status_code == 200
    assert response.json()["text"] == "Updated text"


def test_update_note_can_clear_medicine_association(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]
    note_id = create_note(client, headers, medicine_id=medicine_id).json()["id"]

    response = client.patch(
        f"/api/v1/health-notes/{note_id}", headers=headers, json={"medicine_id": None}
    )

    assert response.status_code == 200
    assert response.json()["medicine_id"] is None


def test_update_note_rejects_medicine_not_owned(client):
    headers_a = register_and_login(client, email="a@example.com")
    headers_b = register_and_login(client, email="b@example.com")
    medicine_id = create_medicine(client, headers_a).json()["id"]
    note_id = create_note(client, headers_b).json()["id"]

    response = client.patch(
        f"/api/v1/health-notes/{note_id}", headers=headers_b, json={"medicine_id": medicine_id}
    )

    assert response.status_code == 400


def test_delete_note_actually_removes_it(client):
    headers = register_and_login(client)
    note_id = create_note(client, headers).json()["id"]

    delete_response = client.delete(f"/api/v1/health-notes/{note_id}", headers=headers)
    get_response = client.get(f"/api/v1/health-notes/{note_id}", headers=headers)

    assert delete_response.status_code == 204
    assert get_response.status_code == 404  # really gone, not archived


def test_patient_a_cannot_access_patient_bs_note(client):
    headers_a = register_and_login(client, email="a@example.com")
    headers_b = register_and_login(client, email="b@example.com")
    note_id = create_note(client, headers_a).json()["id"]

    get_response = client.get(f"/api/v1/health-notes/{note_id}", headers=headers_b)
    patch_response = client.patch(
        f"/api/v1/health-notes/{note_id}", headers=headers_b, json={"text": "hijacked"}
    )
    delete_response = client.delete(f"/api/v1/health-notes/{note_id}", headers=headers_b)

    assert get_response.status_code == 404
    assert patch_response.status_code == 404
    assert delete_response.status_code == 404


def test_health_notes_require_auth(client):
    assert client.get("/api/v1/health-notes").status_code == 401
    assert client.post("/api/v1/health-notes", json={"text": "x"}).status_code == 401
