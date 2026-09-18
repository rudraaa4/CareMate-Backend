from tests.conftest import register_and_login
from tests.test_medicines import create_medicine


def create_schedule(client, headers, medicine_id, **overrides):
    payload = {"time_of_day": "08:00:00", "start_date": "2026-01-01"}
    payload.update(overrides)
    return client.post(f"/api/v1/medicines/{medicine_id}/schedules", headers=headers, json=payload)


def test_create_schedule_for_owned_medicine(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]

    response = create_schedule(client, headers, medicine_id, time_of_day="08:00:00")

    assert response.status_code == 201
    body = response.json()
    assert body["medicine_id"] == medicine_id
    assert body["time_of_day"] == "08:00:00"
    assert body["frequency"] == "daily"
    assert body["active"] is True


def test_medicine_can_have_multiple_schedule_times(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]
    create_schedule(client, headers, medicine_id, time_of_day="08:00:00")
    create_schedule(client, headers, medicine_id, time_of_day="20:00:00")

    response = client.get(f"/api/v1/medicines/{medicine_id}/schedules", headers=headers)

    times = [s["time_of_day"] for s in response.json()]
    assert times == ["08:00:00", "20:00:00"]  # ordered by time_of_day


def test_cannot_create_schedule_on_another_patients_medicine(client):
    headers_a = register_and_login(client, email="a@example.com")
    headers_b = register_and_login(client, email="b@example.com")
    medicine_id = create_medicine(client, headers_a).json()["id"]

    response = create_schedule(client, headers_b, medicine_id)

    assert response.status_code == 404


def test_update_schedule(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]
    schedule_id = create_schedule(client, headers, medicine_id, time_of_day="08:00:00").json()["id"]

    response = client.patch(
        f"/api/v1/schedules/{schedule_id}", headers=headers, json={"time_of_day": "09:30:00"}
    )

    assert response.status_code == 200
    assert response.json()["time_of_day"] == "09:30:00"


def test_archive_schedule(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]
    schedule_id = create_schedule(client, headers, medicine_id).json()["id"]

    response = client.delete(f"/api/v1/schedules/{schedule_id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["active"] is False

    # archived schedules disappear from the default list
    listing = client.get(f"/api/v1/medicines/{medicine_id}/schedules", headers=headers)
    assert listing.json() == []


def test_patient_a_cannot_modify_patient_bs_schedule(client):
    """The two-level ownership chain (Schedule -> Medicine -> Patient) must
    still block cross-patient access, exactly like Phase 5's medicines."""
    headers_a = register_and_login(client, email="a@example.com")
    headers_b = register_and_login(client, email="b@example.com")
    medicine_id = create_medicine(client, headers_a).json()["id"]
    schedule_id = create_schedule(client, headers_a, medicine_id).json()["id"]

    patch_response = client.patch(
        f"/api/v1/schedules/{schedule_id}", headers=headers_b, json={"time_of_day": "23:00:00"}
    )
    delete_response = client.delete(f"/api/v1/schedules/{schedule_id}", headers=headers_b)

    assert patch_response.status_code == 404
    assert delete_response.status_code == 404


def test_schedules_require_auth(client):
    assert client.get("/api/v1/medicines/1/schedules").status_code == 401
    assert client.patch("/api/v1/schedules/1", json={}).status_code == 401
