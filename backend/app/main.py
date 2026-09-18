from fastapi import FastAPI

app = FastAPI(title="CareMate API")


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "UP", "service": "CareMate API"}
