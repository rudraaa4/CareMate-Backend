from datetime import timedelta

from app.core.timezone import local_now
from app.services.adherence_service import AdherenceService
from tests.conftest import register_and_login
from tests.test_inventory import create_inventory
from tests.test_medicines import create_medicine
from tests.test_schedules import create_schedule


def test_dashboard_requires_auth(client):
    assert client.get("/api/v1/dashboard").status_code == 401


def test_dashboard_empty_state_for_new_patient(client):
    headers = register_and_login(client)

    response = client.get("/api/v1/dashboard", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["today"] == {"scheduled": 0, "taken": 0, "remaining": 0}
    assert body["adherence_percentage"] is None
    assert body["low_stock_count"] == 0
    assert body["active_medicines"] == 0


def test_dashboard_reflects_scheduled_and_remaining(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]
    future_time = (local_now() + timedelta(hours=1)).strftime("%H:%M:00")
    create_schedule(client, headers, medicine_id, time_of_day=future_time)

    response = client.get("/api/v1/dashboard", headers=headers)

    body = response.json()
    assert body["today"] == {"scheduled": 1, "taken": 0, "remaining": 1}


def test_dashboard_reflects_taken_events(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]
    create_schedule(client, headers, medicine_id)  # default 08:00 — likely already due
    event_id = client.get("/api/v1/medication-events/today", headers=headers).json()[0]["id"]
    client.patch(f"/api/v1/medication-events/{event_id}/status", headers=headers, json={"status": "taken"})

    response = client.get("/api/v1/dashboard", headers=headers)

    body = response.json()
    assert body["today"]["scheduled"] == 1
    assert body["today"]["taken"] == 1
    assert body["today"]["remaining"] == 0


def test_dashboard_adherence_matches_adherence_service_directly(client, db):
    headers = register_and_login(client, email="checked@example.com")
    patient_id = client.get("/api/v1/profile", headers=headers).json()["id"]
    medicine_id = create_medicine(client, headers).json()["id"]
    create_schedule(client, headers, medicine_id)
    event_id = client.get("/api/v1/medication-events/today", headers=headers).json()[0]["id"]
    client.patch(f"/api/v1/medication-events/{event_id}/status", headers=headers, json={"status": "taken"})

    expected = AdherenceService(db, patient_id).get_weekly_summary().adherence_percentage
    response = client.get("/api/v1/dashboard", headers=headers)

    assert response.json()["adherence_percentage"] == expected


def test_dashboard_low_stock_count(client):
    headers = register_and_login(client)
    low_medicine_id = create_medicine(client, headers, name="Low Stock Med").json()["id"]
    ok_medicine_id = create_medicine(client, headers, name="Well Stocked Med").json()["id"]
    create_inventory(client, headers, low_medicine_id, current_quantity=2, low_stock_threshold=5)
    create_inventory(client, headers, ok_medicine_id, current_quantity=50, low_stock_threshold=5)

    response = client.get("/api/v1/dashboard", headers=headers)

    assert response.json()["low_stock_count"] == 1


def test_dashboard_active_medicines_excludes_archived(client):
    headers = register_and_login(client)
    active_id = create_medicine(client, headers, name="Active").json()["id"]
    archived_id = create_medicine(client, headers, name="Archived").json()["id"]
    client.delete(f"/api/v1/medicines/{archived_id}", headers=headers)

    response = client.get("/api/v1/dashboard", headers=headers)

    assert response.json()["active_medicines"] == 1


def test_dashboard_is_isolated_per_patient(client):
    headers_a = register_and_login(client, email="a@example.com")
    headers_b = register_and_login(client, email="b@example.com")
    create_medicine(client, headers_a)  # A has 1 medicine, B has none

    response_a = client.get("/api/v1/dashboard", headers=headers_a)
    response_b = client.get("/api/v1/dashboard", headers=headers_b)

    assert response_a.json()["active_medicines"] == 1
    assert response_b.json()["active_medicines"] == 0
