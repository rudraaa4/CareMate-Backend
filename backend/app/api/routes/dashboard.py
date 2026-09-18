from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.medication_event import MedicationEventStatus
from app.models.medicine import Medicine
from app.models.user import User
from app.schemas.dashboard import DashboardResponse, TodaySummary
from app.services.adherence_service import ADHERENT_STATUSES, AdherenceService
from app.services.inventory_service import InventoryService
from app.services.medication_event_service import get_or_create_todays_events

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> DashboardResponse:
    patient_id = current_user.patient_profile.id

    # Same query Phase 7's GET /medication-events/today uses — imported,
    # not re-derived, so "today's events" has exactly one definition.
    events = get_or_create_todays_events(patient_id, db)
    taken_count = sum(1 for event in events if event.status in ADHERENT_STATUSES)
    remaining_count = sum(1 for event in events if event.status == MedicationEventStatus.UPCOMING)

    # Rolling 7-day window rather than literally "today" — early in the
    # day, today's own figure would look artificially perfect (doses not
    # yet due aren't counted as eligible, so 100% is common and not
    # meaningful). A trailing week is a more honest headline number.
    weekly_adherence = AdherenceService(db, patient_id).get_weekly_summary()

    low_stock_count = InventoryService(db).count_low_stock_for_patient(patient_id)

    # A plain count, not business logic — doesn't warrant a service method.
    active_medicines = (
        db.query(Medicine)
        .filter(Medicine.patient_id == patient_id, Medicine.active.is_(True))
        .count()
    )

    return DashboardResponse(
        today=TodaySummary(scheduled=len(events), taken=taken_count, remaining=remaining_count),
        adherence_percentage=weekly_adherence.adherence_percentage,
        low_stock_count=low_stock_count,
        active_medicines=active_medicines,
    )
