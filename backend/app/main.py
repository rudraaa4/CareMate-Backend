from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.routes.auth import router as auth_router
from app.api.routes.medication_events import router as medication_events_router
from app.api.routes.medicines import router as medicines_router
from app.api.routes.profile import router as profile_router
from app.api.routes.schedules import router as schedules_router
from app.api.routes.users import router as users_router
from app.core.config import settings
from app.core.database import get_db

app = FastAPI(title="CareMate API")

# Browsers block JS on one origin (scheme+host+port) from reading responses
# from a different origin unless the server opts in via these headers. Our
# API (port 8000) and the dev API-tester page (port 8080) count as different
# origins, so without this, every fetch() from that page would be blocked
# client-side even though the request succeeded on the server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(profile_router)
app.include_router(medicines_router)
app.include_router(schedules_router)
app.include_router(medication_events_router)


@app.get("/api/health")
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "UP", "service": "CareMate API", "database": "UP"}
