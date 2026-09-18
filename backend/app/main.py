from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.core.database import get_db

app = FastAPI(title="CareMate API")

app.include_router(auth_router)
app.include_router(users_router)


@app.get("/api/health")
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "UP", "service": "CareMate API", "database": "UP"}
