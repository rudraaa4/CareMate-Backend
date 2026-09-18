"""Inventory arithmetic — deliberately deterministic, no AI (per spec:
"Gemini is NOT needed" for this phase).
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.medication_schedule import MedicationSchedule
from app.models.medicine import Medicine
from app.models.medicine_inventory import MedicineInventory


@dataclass
class InventoryCalculations:
    estimated_doses_remaining: float
    estimated_days_remaining: float | None
    low_stock: bool


class InventoryService:
    def __init__(self, db: Session):
        self.db = db

    def get_for_medicine(self, medicine_id: int) -> MedicineInventory | None:
        return (
            self.db.query(MedicineInventory)
            .filter(MedicineInventory.medicine_id == medicine_id)
            .first()
        )

    def decrement_for_taken_event(self, medicine_id: int) -> None:
        """Called exactly once per event, from
        medication_event_service.mark_taken() — only reachable when an
        event transitions OUT of a non-terminal status, which (per Phase
        7's TERMINAL_STATUSES guard) can only happen once per event under
        normal sequential use. No-op if the medicine has no inventory
        record — inventory tracking is opt-in, not mandatory.

        Known limitation: this doesn't defend against a true concurrent
        race (two simultaneous requests both passing the "not yet
        terminal" check before either commits) — that needs row-level
        locking, which is Phase 32 hardening territory, not this phase.
        """
        inventory = self.get_for_medicine(medicine_id)
        if inventory is None:
            return
        # Clamp at 0 — logging more doses than physically remained
        # shouldn't produce a negative, confusing stock count.
        inventory.current_quantity = max(0.0, inventory.current_quantity - inventory.units_per_dose)
        self.db.commit()

    def calculate(self, inventory: MedicineInventory) -> InventoryCalculations:
        doses_remaining = inventory.current_quantity / inventory.units_per_dose

        # Only DAILY frequency exists so far (Phase 6 decision) — so each
        # active schedule row is exactly one dose per day. This naturally
        # needs revisiting if/when WEEKLY etc. are added.
        doses_per_day = (
            self.db.query(MedicationSchedule)
            .filter(
                MedicationSchedule.medicine_id == inventory.medicine_id,
                MedicationSchedule.active.is_(True),
            )
            .count()
        )
        days_remaining = doses_remaining / doses_per_day if doses_per_day > 0 else None

        return InventoryCalculations(
            estimated_doses_remaining=doses_remaining,
            estimated_days_remaining=days_remaining,
            low_stock=inventory.current_quantity <= inventory.low_stock_threshold,
        )

    def count_low_stock_for_patient(self, patient_id: int) -> int:
        """Used by the Phase 10 dashboard — reuses calculate() rather than
        re-deriving the low_stock condition, so there's one definition of
        'low stock' in the whole codebase."""
        inventories = (
            self.db.query(MedicineInventory)
            .join(Medicine, MedicineInventory.medicine_id == Medicine.id)
            .filter(Medicine.patient_id == patient_id, Medicine.active.is_(True))
            .all()
        )
        return sum(1 for inventory in inventories if self.calculate(inventory).low_stock)
