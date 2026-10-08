from datetime import datetime

from app.core.timezone import local_now
from app.models.medication_event import MedicationEventStatus
from tests.conftest import register_and_login
from tests.test_adherence_service import seed_event
from tests.test_documents import upload
from tests.test_health_notes import create_note
from tests.test_medicines import create_medicine
from tests.test_prescriptions import create_prescription
from tests.test_schedules import create_schedule


def get_timeline(client, headers, **params):
    return client.get("/api/v1/timeline", headers=headers, params=params)


def items_of_type(response, item_type):
    return [item for item in response.json()["items"] if item["type"] == item_type]


def test_timeline_requires_auth(client):
    assert client.get("/api/v1/timeline").status_code == 401


def test_new_patient_has_empty_timeline(client):
    headers = register_and_login(client)

    response = get_timeline(client, headers)

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_treatment_start_and_end_come_from_medicine_dates(client):
    headers = register_and_login(client)
    create_medicine(client, headers, start_date="2026-01-05", end_date="2026-02-20")

    response = get_timeline(client, headers, order="asc")

    items = response.json()["items"]
    assert [i["type"] for i in items] == ["treatment_started", "treatment_ended"]
    assert items[0]["title"] == "Started Metformin 500mg"
    assert items[0]["occurred_at"].startswith("2026-01-05")
    assert items[1]["title"] == "Ended Metformin 500mg"
    assert items[1]["occurred_at"].startswith("2026-02-20")


def test_medicine_without_start_date_appears_on_day_it_was_added(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]

    started = items_of_type(get_timeline(client, headers), "treatment_started")

    assert len(started) == 1
    assert started[0]["reference_id"] == medicine_id
    assert started[0]["occurred_at"].startswith(local_now().date().isoformat())


def test_prescription_item_carries_doctor_and_document(client):
    headers = register_and_login(client)
    document_id = upload(client, headers, document_type="prescription").json()["id"]
    prescription_id = create_prescription(
        client,
        headers,
        prescription_date="2026-03-02",
        doctor_name="Dr. Rao",
        hospital_name="City Clinic",
        document_id=document_id,
    ).json()["id"]

    response = get_timeline(client, headers)

    prescriptions = items_of_type(response, "prescription")
    assert len(prescriptions) == 1
    assert prescriptions[0]["title"] == "Prescription from Dr. Rao"
    assert prescriptions[0]["description"] == "City Clinic"
    assert prescriptions[0]["reference_id"] == prescription_id
    assert prescriptions[0]["document_id"] == document_id
    # the linked file is part of the prescription item, not listed twice
    assert items_of_type(response, "document") == []


def test_standalone_document_uses_document_date_when_given(client):
    headers = register_and_login(client)
    upload(client, headers, document_type="lab_report", document_date="2026-02-10")

    documents = items_of_type(get_timeline(client, headers), "document")

    assert len(documents) == 1
    assert documents[0]["title"] == "Lab report uploaded"
    assert documents[0]["occurred_at"].startswith("2026-02-10")
    assert documents[0]["document_id"] == documents[0]["reference_id"]


def test_health_note_names_its_medicine(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]
    create_note(client, headers, text="Mild nausea", medicine_id=medicine_id)
    create_note(client, headers, text="Feeling better")

    notes = items_of_type(get_timeline(client, headers), "health_note")

    titles = {n["title"]: n["description"] for n in notes}
    assert titles == {"Note about Metformin": "Mild nausea", "Health note": "Feeling better"}


def test_monthly_adherence_summary(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]
    schedule_id = create_schedule(client, headers, medicine_id).json()["id"]
    tz = local_now().tzinfo
    for day, status in [
        (12, MedicationEventStatus.TAKEN),
        (13, MedicationEventStatus.TAKEN),
        (14, MedicationEventStatus.TAKEN),
        (15, MedicationEventStatus.MISSED),
    ]:
        seed_event(schedule_id, datetime(2026, 1, day, 8, 0, tzinfo=tz), status)

    summaries = items_of_type(get_timeline(client, headers), "adherence_summary")

    january = [s for s in summaries if "January 2026" in s["title"]]
    assert len(january) == 1
    assert january[0]["title"] == "75% adherence in January 2026"
    assert january[0]["description"] == "3 of 4 doses taken, 1 missed"
    assert january[0]["occurred_at"].startswith("2026-01-31")
    assert january[0]["reference_id"] is None


def test_months_without_doses_produce_no_summary(client):
    headers = register_and_login(client)
    medicine_id = create_medicine(client, headers).json()["id"]
    schedule_id = create_schedule(client, headers, medicine_id).json()["id"]
    tz = local_now().tzinfo
    seed_event(schedule_id, datetime(2026, 1, 12, 8, 0, tzinfo=tz), MedicationEventStatus.TAKEN)
    seed_event(schedule_id, datetime(2026, 3, 12, 8, 0, tzinfo=tz), MedicationEventStatus.TAKEN)

    summaries = items_of_type(get_timeline(client, headers), "adherence_summary")

    titles = [s["title"] for s in summaries]
    assert any("January 2026" in t for t in titles)
    assert any("March 2026" in t for t in titles)
    assert not any("February 2026" in t for t in titles)


def test_order_param_controls_direction(client):
    headers = register_and_login(client)
    create_prescription(client, headers, prescription_date="2026-01-10")
    create_prescription(client, headers, prescription_date="2026-03-05")
    create_prescription(client, headers, prescription_date="2026-02-01")

    newest_first = [i["occurred_at"][:10] for i in items_of_type(get_timeline(client, headers), "prescription")]
    oldest_first = [
        i["occurred_at"][:10]
        for i in items_of_type(get_timeline(client, headers, order="asc"), "prescription")
    ]

    assert newest_first == ["2026-03-05", "2026-02-01", "2026-01-10"]
    assert oldest_first == ["2026-01-10", "2026-02-01", "2026-03-05"]


def test_whole_timeline_is_sorted(client):
    headers = register_and_login(client)
    create_medicine(client, headers, start_date="2026-01-05")
    create_prescription(client, headers, prescription_date="2026-02-01")
    upload(client, headers, document_type="lab_report", document_date="2026-03-01")

    dates = [i["occurred_at"] for i in get_timeline(client, headers, order="asc").json()["items"]]

    assert dates == sorted(dates)


def test_invalid_order_is_rejected(client):
    headers = register_and_login(client)

    assert get_timeline(client, headers, order="sideways").status_code == 422


def test_timeline_only_contains_own_records(client):
    headers_a = register_and_login(client, email="a@example.com")
    headers_b = register_and_login(client, email="b@example.com")
    create_medicine(client, headers_a, name="PrivateMed")
    create_prescription(client, headers_a, doctor_name="Dr. Private")
    create_note(client, headers_a, text="private note")
    upload(client, headers_a, document_type="lab_report")

    response = get_timeline(client, headers_b)

    assert response.json() == {"items": []}
