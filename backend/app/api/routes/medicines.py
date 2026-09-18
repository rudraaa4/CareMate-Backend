from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.medicine import Medicine
from app.models.user import User
from app.schemas.medicine import MedicineCreate, MedicineResponse, MedicineUpdate

router = APIRouter(prefix="/api/v1/medicines", tags=["Medicines"])


def get_owned_medicine(
    medicine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Medicine:
    """Fetches a medicine only if it belongs to the authenticated patient.

    FastAPI matches `medicine_id` here against the {medicine_id} path
    parameter automatically, so every route below just declares
    `Depends(get_owned_medicine)` instead of repeating this lookup.

    Returns 404 (not 403) when the medicine belongs to someone else —
    a 403 would confirm the medicine exists, which is itself information
    Patient B shouldn't get about Patient A's records.
    """
    medicine = (
        db.query(Medicine)
        .filter(
            Medicine.id == medicine_id,
            Medicine.patient_id == current_user.patient_profile.id,
        )
        .first()
    )
    if medicine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found")
    return medicine


@router.post("", response_model=MedicineResponse, status_code=status.HTTP_201_CREATED)
def create_medicine(
    medicine_in: MedicineCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Medicine:
    medicine = Medicine(patient_id=current_user.patient_profile.id, **medicine_in.model_dump())
    db.add(medicine)
    db.commit()
    db.refresh(medicine)
    return medicine


@router.get("", response_model=list[MedicineResponse])
def list_medicines(
    include_archived: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Medicine]:
    query = db.query(Medicine).filter(Medicine.patient_id == current_user.patient_profile.id)
    if not include_archived:
        query = query.filter(Medicine.active.is_(True))
    return query.order_by(Medicine.created_at.desc()).all()


@router.get("/{medicine_id}", response_model=MedicineResponse)
def get_medicine(medicine: Medicine = Depends(get_owned_medicine)) -> Medicine:
    return medicine


@router.patch("/{medicine_id}", response_model=MedicineResponse)
def update_medicine(
    medicine_in: MedicineUpdate,
    medicine: Medicine = Depends(get_owned_medicine),
    db: Session = Depends(get_db),
) -> Medicine:
    updates = medicine_in.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(medicine, field, value)
    db.commit()
    db.refresh(medicine)
    return medicine


@router.delete("/{medicine_id}", response_model=MedicineResponse)
def archive_medicine(
    medicine: Medicine = Depends(get_owned_medicine), db: Session = Depends(get_db)
) -> Medicine:
    medicine.active = False
    db.commit()
    db.refresh(medicine)
    return medicine
