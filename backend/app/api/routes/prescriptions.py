from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.medical_document import DocumentType, MedicalDocument
from app.models.prescription import Prescription, PrescriptionSource
from app.models.user import User
from app.schemas.prescription import PrescriptionCreate, PrescriptionResponse, PrescriptionUpdate

router = APIRouter(prefix="/api/v1/prescriptions", tags=["Prescriptions"])


def _validate_document(document_id: int | None, patient_id: int, db: Session) -> None:
    """document_id arrives in the request body, so a client could try to
    attach someone else's file, or a lab report that is not a prescription.
    Both are 400 (invalid request value); 404 stays reserved for the
    prescription in the URL."""
    if document_id is None:
        return
    document = (
        db.query(MedicalDocument)
        .filter(MedicalDocument.id == document_id, MedicalDocument.patient_id == patient_id)
        .first()
    )
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="document_id does not refer to one of your documents",
        )
    if document.document_type != DocumentType.PRESCRIPTION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="document_id must refer to a document of type 'prescription'",
        )


def _source_for(document_id: int | None) -> PrescriptionSource:
    return PrescriptionSource.MANUAL if document_id is None else PrescriptionSource.DOCUMENT_UPLOAD


def get_owned_prescription(
    prescription_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Prescription:
    prescription = (
        db.query(Prescription)
        .filter(
            Prescription.id == prescription_id,
            Prescription.patient_id == current_user.patient_profile.id,
        )
        .first()
    )
    if prescription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")
    return prescription


@router.post("", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED)
def create_prescription(
    prescription_in: PrescriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Prescription:
    patient_id = current_user.patient_profile.id
    _validate_document(prescription_in.document_id, patient_id, db)

    prescription = Prescription(
        patient_id=patient_id,
        source=_source_for(prescription_in.document_id),
        **prescription_in.model_dump(),
    )
    db.add(prescription)
    db.commit()
    db.refresh(prescription)
    return prescription


@router.get("", response_model=list[PrescriptionResponse])
def list_prescriptions(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Prescription]:
    return (
        db.query(Prescription)
        .filter(Prescription.patient_id == current_user.patient_profile.id)
        .order_by(Prescription.prescription_date.desc(), Prescription.id.desc())
        .all()
    )


@router.get("/{prescription_id}", response_model=PrescriptionResponse)
def get_prescription(
    prescription: Prescription = Depends(get_owned_prescription),
) -> Prescription:
    return prescription


@router.patch("/{prescription_id}", response_model=PrescriptionResponse)
def update_prescription(
    prescription_in: PrescriptionUpdate,
    prescription: Prescription = Depends(get_owned_prescription),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Prescription:
    updates = prescription_in.model_dump(exclude_unset=True)
    if "document_id" in updates:
        _validate_document(updates["document_id"], current_user.patient_profile.id, db)
        prescription.source = _source_for(updates["document_id"])

    for field, value in updates.items():
        setattr(prescription, field, value)

    db.commit()
    db.refresh(prescription)
    return prescription


@router.delete("/{prescription_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prescription(
    prescription: Prescription = Depends(get_owned_prescription), db: Session = Depends(get_db)
) -> None:
    # Real delete, like health notes. The linked document (if any) is a
    # separate record and is left untouched.
    db.delete(prescription)
    db.commit()
