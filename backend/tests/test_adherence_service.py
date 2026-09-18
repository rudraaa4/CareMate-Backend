from datetime import timedelta

from app.core.timezone import local_now
from app.models.medication_event import MedicationEvent, MedicationEventStatus
from app.services.adherence_service import AdherenceService
from tests.conftest import TestingSessionLocal, register_and_login
from tests.test_medicines import create_medicine
from tests.test_schedules import create_schedule


def setup_patient_with_schedule(client, email="patient@example.com"):
    headers = register_and_login(client, email=email)
    patient_id = client.get("/api/v1/profile", headers=headers).json()["id"]
    medicine_id = create_medicine(client, headers).json()["id"]
    schedule_id = create_schedule(client, headers, medicine_id).json()["id"]
    return patient_id, schedule_id


def seed_event(schedule_id, scheduled_at, status, actual_taken_at=None):
    db = TestingSessionLocal()
    try:
        db.add(
            MedicationEvent(
                schedule_id=schedule_id,
                scheduled_at=scheduled_at,
                status=status,
                actual_taken_at=actual_taken_at,
            )
        )
        db.commit()
    finally:
        db.close()


def test_zero_events_gives_no_adherence_percentage(client, db):
    patient_id, _ = setup_patient_with_schedule(client)
    today = local_now().date()

    summary = AdherenceService(db, patient_id).calculate_period_adherence(today, today)

    assert summary.expected_doses == 0
    assert summary.adherence_percentage is None


def test_all_taken_is_full_adherence(client, db):
    patient_id, schedule_id = setup_patient_with_schedule(client)
    today = local_now().date()
    base = local_now().replace(hour=8, minute=0, second=0, microsecond=0)
    for hour_offset in range(4):
        seed_event(
            schedule_id,
            base + timedelta(hours=hour_offset),
            MedicationEventStatus.TAKEN,
            actual_taken_at=base + timedelta(hours=hour_offset),
        )

    summary = AdherenceService(db, patient_id).calculate_period_adherence(today, today)

    assert summary.expected_doses == 4
    assert summary.taken_doses == 4
    assert summary.adherence_percentage == 100.0


def test_delayed_counts_as_taken_but_is_reported_separately(client, db):
    patient_id, schedule_id = setup_patient_with_schedule(client)
    today = local_now().date()
    base = local_now().replace(hour=8, minute=0, second=0, microsecond=0)
    seed_event(schedule_id, base, MedicationEventStatus.TAKEN, actual_taken_at=base)
    seed_event(schedule_id, base + timedelta(hours=1), MedicationEventStatus.DELAYED, actual_taken_at=base)

    summary = AdherenceService(db, patient_id).calculate_period_adherence(today, today)

    assert summary.expected_doses == 2
    assert summary.taken_doses == 2  # DELAYED counted as taken
    assert summary.delayed_doses == 1  # but still visible separately
    assert summary.adherence_percentage == 100.0


def test_missed_and_skipped_reduce_percentage(client, db):
    patient_id, schedule_id = setup_patient_with_schedule(client)
    today = local_now().date()
    base = local_now().replace(hour=8, minute=0, second=0, microsecond=0)
    for i in range(5):
        seed_event(schedule_id, base + timedelta(hours=i), MedicationEventStatus.TAKEN, actual_taken_at=base)
    seed_event(schedule_id, base + timedelta(hours=5), MedicationEventStatus.MISSED)
    seed_event(schedule_id, base + timedelta(hours=6), MedicationEventStatus.MISSED)
    seed_event(schedule_id, base + timedelta(hours=7), MedicationEventStatus.SKIPPED)

    summary = AdherenceService(db, patient_id).calculate_period_adherence(today, today)

    assert summary.expected_doses == 8
    assert summary.taken_doses == 5
    assert summary.missed_doses == 2
    assert summary.skipped_doses == 1
    assert summary.adherence_percentage == 62.5


def test_upcoming_events_are_excluded_from_calculation(client, db):
    patient_id, schedule_id = setup_patient_with_schedule(client)
    today = local_now().date()
    base = local_now().replace(hour=8, minute=0, second=0, microsecond=0)
    seed_event(schedule_id, base, MedicationEventStatus.TAKEN, actual_taken_at=base)
    # scheduled later today, hasn't happened yet
    seed_event(schedule_id, local_now() + timedelta(hours=2), MedicationEventStatus.UPCOMING)

    summary = AdherenceService(db, patient_id).calculate_period_adherence(today, today)

    assert summary.expected_doses == 1  # the UPCOMING one doesn't count yet
    assert summary.adherence_percentage == 100.0


def test_stale_upcoming_event_is_treated_as_missed(client, db):
    """An UPCOMING event nobody ever fetched via the API (so it was never
    lazily flipped to MISSED) must still be counted correctly here — the
    whole reason refresh_missed_statuses was promoted into a shared
    service rather than left private to the routes file."""
    patient_id, schedule_id = setup_patient_with_schedule(client)
    today = local_now().date()
    seed_event(schedule_id, local_now() - timedelta(hours=5), MedicationEventStatus.UPCOMING)

    summary = AdherenceService(db, patient_id).calculate_period_adherence(today, today)

    assert summary.expected_doses == 1
    assert summary.missed_doses == 1


def test_get_daily_summary_scopes_to_one_day(client, db):
    patient_id, schedule_id = setup_patient_with_schedule(client)
    today = local_now().date()
    base_today = local_now().replace(hour=8, minute=0, second=0, microsecond=0)
    base_yesterday = base_today - timedelta(days=1)
    seed_event(schedule_id, base_today, MedicationEventStatus.TAKEN, actual_taken_at=base_today)
    seed_event(schedule_id, base_yesterday, MedicationEventStatus.MISSED)

    summary = AdherenceService(db, patient_id).get_daily_summary(today)

    assert summary.expected_doses == 1
    assert summary.taken_doses == 1


def test_get_weekly_summary_covers_seven_days_only(client, db):
    patient_id, schedule_id = setup_patient_with_schedule(client)
    today = local_now().date()
    base = local_now().replace(hour=8, minute=0, second=0, microsecond=0)
    for days_ago in range(10):  # 10 days of history
        seed_event(
            schedule_id, base - timedelta(days=days_ago), MedicationEventStatus.TAKEN, actual_taken_at=base
        )

    summary = AdherenceService(db, patient_id).get_weekly_summary(today)

    assert summary.expected_doses == 7  # only the last 7 days, not all 10
    assert summary.taken_doses == 7
