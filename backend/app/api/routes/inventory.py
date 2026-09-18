from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.medicines import get_owned_medicine
from app.core.database import get_db
from app.models.medicine import Medicine
from app.models.medicine_inventory import MedicineInventory
from app.schemas.medicine_inventory import (
    MedicineInventoryCreate,
    MedicineInventoryResponse,
    MedicineInventoryUpdate,
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/api/v1/medicines/{medicine_id}/inventory", tags=["Medicine Inventory"])


def _build_response(inventory: MedicineInventory, db: Session) -> MedicineInventoryResponse:
    calc = InventoryService(db).calculate(inventory)
    return MedicineInventoryResponse(
        id=inventory.id,
        medicine_id=inventory.medicine_id,
        current_quantity=inventory.current_quantity,
        units_per_dose=inventory.units_per_dose,
        low_stock_threshold=inventory.low_stock_threshold,
        estimated_doses_remaining=calc.estimated_doses_remaining,
        estimated_days_remaining=calc.estimated_days_remaining,
        low_stock=calc.low_stock,
        updated_at=inventory.updated_at,
    )


def _get_or_404(medicine_id: int, db: Session) -> MedicineInventory:
    inventory = InventoryService(db).get_for_medicine(medicine_id)
    if inventory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory has not been set up for this medicine yet",
        )
    return inventory


@router.post("", response_model=MedicineInventoryResponse, status_code=status.HTTP_201_CREATED)
def create_inventory(
    data: MedicineInventoryCreate,
    medicine: Medicine = Depends(get_owned_medicine),
    db: Session = Depends(get_db),
) -> MedicineInventoryResponse:
    if InventoryService(db).get_for_medicine(medicine.id) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Inventory already exists for this medicine",
        )

    inventory = MedicineInventory(medicine_id=medicine.id, **data.model_dump())
    db.add(inventory)
    db.commit()
    db.refresh(inventory)
    return _build_response(inventory, db)


@router.get("", response_model=MedicineInventoryResponse)
def get_inventory(
    medicine: Medicine = Depends(get_owned_medicine), db: Session = Depends(get_db)
) -> MedicineInventoryResponse:
    inventory = _get_or_404(medicine.id, db)
    return _build_response(inventory, db)


@router.patch("", response_model=MedicineInventoryResponse)
def update_inventory(
    data: MedicineInventoryUpdate,
    medicine: Medicine = Depends(get_owned_medicine),
    db: Session = Depends(get_db),
) -> MedicineInventoryResponse:
    inventory = _get_or_404(medicine.id, db)
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(inventory, field, value)
    db.commit()
    db.refresh(inventory)
    return _build_response(inventory, db)
