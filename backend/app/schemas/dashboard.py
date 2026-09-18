from pydantic import BaseModel


class TodaySummary(BaseModel):
    scheduled: int
    taken: int
    remaining: int


class DashboardResponse(BaseModel):
    today: TodaySummary
    # 7-day rolling window, not literally today — see
    # app/api/routes/dashboard.py for why.
    adherence_percentage: float | None
    low_stock_count: int
    active_medicines: int
