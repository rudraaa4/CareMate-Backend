from datetime import timedelta

from app.core.timezone import local_now as _local_now
from app.models.medication_event import MedicationEvent
from tests.conftest import TestingSessionLocal, register_and_login
from tests.test_medicines import create_medicine
from tests.test_schedules import create_schedule


def setup_medicine_with_schedule(client, headers, time_of_day="08:00:00"):
    medicine_id = create_medicine(client, headers).json()["id"]
    schedule_id = create_schedule(client, headers, medicine_id, time_of_day=time_of_day).json()["id"]
    return medicine_id, schedule_id


def force_scheduled_at(event_id: int, scheduled_at) -> None:
    """Directly rewrites an event's scheduled_at in the test DB — used to
    simulate "this was scheduled a while ago" without literally waiting."""
    db = TestingSessionLocal()
    try:
        event = db.get(MedicationEvent, event_id)
        event.scheduled_at = scheduled_at
        db.commit()
    finally:
        db.close()


def test_get_today_events_generates_upcoming_event(client):
    headers = register_and_login(client)
    # Must genuinely be in the near future/recent past relative to whenever
    # the test runs — a fixed clock time like "08:00" would be flagged
    # MISSED if the suite happens to run in the afternoon, which is correct
    # app behavior, just not what this test is checking.
    future_time = (_local_now() + timedelta(hours=1)).strftime("%H:%M:00")
    setup_medicine_with_schedule(client, headers, time_of_day=future_time)

    response = client.get("/api/v1/medication-events/today", headers=headers)

    assert response.status_code == 200
    events = response.json()
    assert len(events) == 1
    assert events[0]["status"] == "upcoming"
    assert events[0]["actual_taken_at"] is None


def test_get_today_events_is_idempotent(client):
    headers = register_and_login(client)
    setup_medicine_with_schedule(client, headers)

    client.get("/api/v1/medication-events/today", headers=headers)
    second = client.get("/api/v1/medication-events/today", headers=headers)

    assert len(second.json()) == 1  # not duplicated


def test_mark_event_taken_on_time(client):
    headers = register_and_login(client)
    now = _local_now()
    setup_medicine_with_schedule(client, headers, time_of_day=now.strftime("%H:%M:00"))
    event_id = client.get("/api/v1/medication-events/today", headers=headers).json()[0]["id"]

    response = client.patch(
        f"/api/v1/medication-events/{event_id}/status", headers=headers, json={"status": "taken"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "taken"
    assert body["actual_taken_at"] is not None


def test_mark_event_taken_late_becomes_delayed(client):
    headers = register_and_login(client)
    _, _ = setup_medicine_with_schedule(client, headers)
    event_id = client.get("/api/v1/medication-events/today", headers=headers).json()[0]["id"]
    force_scheduled_at(event_id, _local_now() - timedelta(minutes=45))

    response = client.patch(
        f"/api/v1/medication-events/{event_id}/status", headers=headers, json={"status": "taken"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "delayed"


def test_mark_event_skipped(client):
    headers = register_and_login(client)
    setup_medicine_with_schedule(client, headers)
    event_id = client.get("/api/v1/medication-events/today", headers=headers).json()[0]["id"]

    response = client.patch(
        f"/api/v1/medication-events/{event_id}/status",
        headers=headers,
        json={"status": "skipped", "note": "felt nauseous"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "skipped"
    assert body["actual_taken_at"] is None
    assert body["note"] == "felt nauseous"


def test_cannot_change_status_after_taken(client):
    headers = register_and_login(client)
    setup_medicine_with_schedule(client, headers)
    event_id = client.get("/api/v1/medication-events/today", headers=headers).json()[0]["id"]
    client.patch(f"/api/v1/medication-events/{event_id}/status", headers=headers, json={"status": "taken"})

    response = client.patch(
        f"/api/v1/medication-events/{event_id}/status", headers=headers, json={"status": "skipped"}
    )

    assert response.status_code == 409


def test_stale_upcoming_event_becomes_missed_on_fetch(client):
    headers = register_and_login(client)
    setup_medicine_with_schedule(client, headers)
    event_id = client.get("/api/v1/medication-events/today", headers=headers).json()[0]["id"]
    force_scheduled_at(event_id, _local_now() - timedelta(hours=3))

    response = client.get("/api/v1/medication-events/today", headers=headers)

    assert response.json()[0]["status"] == "missed"


def test_missed_event_can_still_be_marked_taken(client):
    """MISSED is system-inferred, not patient-confirmed — unlike TAKEN, it
    must not be a dead end. A patient logging a late dose after the missed
    cutoff should still be able to."""
    headers = register_and_login(client)
    setup_medicine_with_schedule(client, headers)
    event_id = client.get("/api/v1/medication-events/today", headers=headers).json()[0]["id"]
    force_scheduled_at(event_id, _local_now() - timedelta(hours=3))
    client.get("/api/v1/medication-events/today", headers=headers)  # flips it to missed

    response = client.patch(
        f"/api/v1/medication-events/{event_id}/status", headers=headers, json={"status": "taken"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "delayed"  # 3h late is well past the delayed threshold too


def test_patient_a_cannot_access_patient_bs_event(client):
    headers_a = register_and_login(client, email="a@example.com")
    headers_b = register_and_login(client, email="b@example.com")
    setup_medicine_with_schedule(client, headers_a)
    event_id = client.get("/api/v1/medication-events/today", headers=headers_a).json()[0]["id"]

    response = client.patch(
        f"/api/v1/medication-events/{event_id}/status", headers=headers_b, json={"status": "taken"}
    )

    assert response.status_code == 404


def test_medication_events_require_auth(client):
    assert client.get("/api/v1/medication-events/today").status_code == 401
    assert client.patch("/api/v1/medication-events/1/status", json={"status": "taken"}).status_code == 401
