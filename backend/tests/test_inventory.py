from tests.conftest import register_and_login
from tests.test_medicines import create_medicine
from tests.test_schedules import create_schedule


def create_inventory(client, headers, medicine_id, **overrides):
    payload = {"current_quantity": 30, "units_per_dose": 1, "low_stock_threshold": 5}
    payload.update(overrides)
    return client.post(f"/api/v1/medicines/{medicine_id}/inventory", headers=headers, json=payload)


def test_create_inventory(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]

    response = create_inventory(client, headers, medicine_id, current_quantity=30, units_per_dose=1)

    assert response.status_code == 201
    body = response.json()
    assert body["current_quantity"] == 30
    assert body["estimated_doses_remaining"] == 30


def test_cannot_create_duplicate_inventory(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]
    create_inventory(client, headers, medicine_id)

    response = create_inventory(client, headers, medicine_id)

    assert response.status_code == 409


def test_get_inventory_without_setup_returns_404(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]

    response = client.get(f"/api/v1/medicines/{medicine_id}/inventory", headers=headers)

    assert response.status_code == 404


def test_estimated_days_remaining_uses_active_schedule_count(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]
    create_schedule(client, headers, medicine_id, time_of_day="08:00:00")
    create_schedule(client, headers, medicine_id, time_of_day="20:00:00")  # 2 doses/day
    create_inventory(client, headers, medicine_id, current_quantity=20, units_per_dose=1)

    response = client.get(f"/api/v1/medicines/{medicine_id}/inventory", headers=headers)

    body = response.json()
    assert body["estimated_doses_remaining"] == 20
    assert body["estimated_days_remaining"] == 10.0  # 20 doses / 2 per day


def test_days_remaining_is_none_with_no_active_schedule(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]
    create_inventory(client, headers, medicine_id, current_quantity=20)

    response = client.get(f"/api/v1/medicines/{medicine_id}/inventory", headers=headers)

    assert response.json()["estimated_days_remaining"] is None


def test_low_stock_boolean(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]
    create_inventory(client, headers, medicine_id, current_quantity=3, low_stock_threshold=5)

    response = client.get(f"/api/v1/medicines/{medicine_id}/inventory", headers=headers)

    assert response.json()["low_stock"] is True


def test_update_inventory_quantity(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]
    create_inventory(client, headers, medicine_id, current_quantity=10)

    response = client.patch(
        f"/api/v1/medicines/{medicine_id}/inventory", headers=headers, json={"current_quantity": 50}
    )

    assert response.status_code == 200
    assert response.json()["current_quantity"] == 50


def test_taking_a_dose_decrements_inventory_exactly_once(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]
    create_schedule(client, headers, medicine_id)
    create_inventory(client, headers, medicine_id, current_quantity=10, units_per_dose=2)
    event_id = client.get("/api/v1/medication-events/today", headers=headers).json()[0]["id"]

    client.patch(f"/api/v1/medication-events/{event_id}/status", headers=headers, json={"status": "taken"})

    inventory = client.get(f"/api/v1/medicines/{medicine_id}/inventory", headers=headers).json()
    assert inventory["current_quantity"] == 8  # 10 - units_per_dose(2)


def test_skipped_dose_does_not_decrement_inventory(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]
    create_schedule(client, headers, medicine_id)
    create_inventory(client, headers, medicine_id, current_quantity=10)
    event_id = client.get("/api/v1/medication-events/today", headers=headers).json()[0]["id"]

    client.patch(f"/api/v1/medication-events/{event_id}/status", headers=headers, json={"status": "skipped"})

    inventory = client.get(f"/api/v1/medicines/{medicine_id}/inventory", headers=headers).json()
    assert inventory["current_quantity"] == 10  # unchanged


def test_cannot_double_decrement_by_re_marking_taken(client):
    """The core Phase 9 requirement: editing/re-processing a TAKEN event
    must not decrement inventory a second time. In this system that's
    enforced by the terminal-status guard rejecting the second PATCH
    outright (409) before decrement logic ever runs again."""
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]
    create_schedule(client, headers, medicine_id)
    create_inventory(client, headers, medicine_id, current_quantity=10, units_per_dose=1)
    event_id = client.get("/api/v1/medication-events/today", headers=headers).json()[0]["id"]
    client.patch(f"/api/v1/medication-events/{event_id}/status", headers=headers, json={"status": "taken"})

    second_attempt = client.patch(
        f"/api/v1/medication-events/{event_id}/status", headers=headers, json={"status": "taken"}
    )

    assert second_attempt.status_code == 409
    inventory = client.get(f"/api/v1/medicines/{medicine_id}/inventory", headers=headers).json()
    assert inventory["current_quantity"] == 9  # decremented once, not twice


def test_decrement_clamps_at_zero(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]
    create_schedule(client, headers, medicine_id)
    create_inventory(client, headers, medicine_id, current_quantity=0.5, units_per_dose=1)
    event_id = client.get("/api/v1/medication-events/today", headers=headers).json()[0]["id"]

    client.patch(f"/api/v1/medication-events/{event_id}/status", headers=headers, json={"status": "taken"})

    inventory = client.get(f"/api/v1/medicines/{medicine_id}/inventory", headers=headers).json()
    assert inventory["current_quantity"] == 0  # not negative


def test_patient_a_cannot_access_patient_bs_inventory(client):
    headers_a = register_and_login(client, email="a@example.com")
    headers_b = register_and_login(client, email="b@example.com")
    medicine_id = create_medicine(client, headers_a).json()["id"]
    create_inventory(client, headers_a, medicine_id)

    get_response = client.get(f"/api/v1/medicines/{medicine_id}/inventory", headers=headers_b)
    create_response = create_inventory(client, headers_b, medicine_id)

    assert get_response.status_code == 404
    assert create_response.status_code == 404


def test_inventory_requires_auth(client):
    assert client.get("/api/v1/medicines/1/inventory").status_code == 401
