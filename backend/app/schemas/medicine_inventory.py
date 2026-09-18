from datetime import datetime

from pydantic import BaseModel, Field


class MedicineInventoryCreate(BaseModel):
    current_quantity: float = Field(ge=0)
    units_per_dose: float = Field(default=1.0, gt=0)
    low_stock_threshold: float = Field(default=5.0, ge=0)


class MedicineInventoryUpdate(BaseModel):
    current_quantity: float | None = Field(default=None, ge=0)
    units_per_dose: float | None = Field(default=None, gt=0)
    low_stock_threshold: float | None = Field(default=None, ge=0)


class MedicineInventoryResponse(BaseModel):
    # Not from_attributes: estimated_doses_remaining/estimated_days_remaining/
    # low_stock aren't database columns, they're computed at read time by
    # InventoryService — the route builds this explicitly instead.
    id: int
    medicine_id: int
    current_quantity: float
    units_per_dose: float
    low_stock_threshold: float
    estimated_doses_remaining: float
    estimated_days_remaining: float | None
    low_stock: bool
    updated_at: datetime
