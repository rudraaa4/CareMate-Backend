from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.medicine import Medicine


class MedicineInventory(Base):
    __tablename__ = "medicine_inventories"

    id: Mapped[int] = mapped_column(primary_key=True)
    medicine_id: Mapped[int] = mapped_column(
        ForeignKey("medicines.id"), unique=True, nullable=False
    )

    current_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    # How many units one dose consumes (e.g. 1 tablet, 2 tablets, 5 ml).
    units_per_dose: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    low_stock_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=5.0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    medicine: Mapped["Medicine"] = relationship(back_populates="inventory")
