# CareMate

CareMate is an AI-assisted continuity-of-care platform. It is not just a
medicine reminder — it connects what a clinician prescribed with what
actually happens afterward, while keeping the patient in control of their
information.

> "The prescription was only the beginning."

## Problem Being Solved

After a patient leaves a hospital or clinic, care often becomes fragmented:
doses get missed, prescriptions get lost, records end up scattered across
paper and phone galleries, medicine stock runs out unnoticed, and doctors
have little visibility into what happened between appointments. CareMate
aims to close that loop: Doctor -> Prescription -> Patient at Home ->
Adherence -> Inventory -> Records -> Follow-up -> Doctor.

## Architecture

Request flow (backend):

```
Client -> Router -> Service -> Repository / ORM -> PostgreSQL -> Response Schema
```

Full long-term architecture, data model, and phased build plan live in
[`CAREMATE_MASTER_SPEC.md`](./CAREMATE_MASTER_SPEC.md). The project is being
built **one phase at a time**; current progress is tracked in
[`DEVELOPMENT_PROGRESS.md`](./DEVELOPMENT_PROGRESS.md).

## Tech Stack

- Python, FastAPI, Uvicorn
- SQLAlchemy 2.x (ORM) + Alembic (migrations)
- Pydantic (validation/schemas)
- PostgreSQL
- pytest / httpx for testing
- Postman for manual API testing
- Git/GitHub for version control
- React (planned, later phase) for the frontend

## Current Implemented Features

None yet — repository foundation only (Phase 0). See
[`DEVELOPMENT_PROGRESS.md`](./DEVELOPMENT_PROGRESS.md) for live status.

## Local Setup

Backend setup instructions will be added starting in Phase 1, once the
FastAPI app and virtual environment exist. This section will grow to cover:

1. Creating and activating the Python virtual environment
2. Installing dependencies (`backend/requirements.txt`)
3. Running the API with Uvicorn
4. Applying database migrations with Alembic

## Environment Variables

See [`.env.example`](./.env.example) for the current list of expected
environment variables. Never commit a real `.env` file — it is git-ignored.

## Database Migrations

Alembic will be introduced in Phase 2. Commands will be documented here once
migrations exist.

## Tests

```bash
# from backend/, once the virtual environment is set up (Phase 1+)
pytest
```

## API Documentation

Once the FastAPI app is running (Phase 1+), interactive docs are available
at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc`.

## Project Roadmap

See [`CAREMATE_MASTER_SPEC.md`](./CAREMATE_MASTER_SPEC.md) sections 11 and 12
for the full phase list and milestone groupings (Milestone A: FastAPI Core →
Milestone G: Productization).

## Safety / Privacy Limitations

CareMate handles health-related information. At this stage (Phase 0) no
patient data is stored anywhere — there is no application yet. Security
principles the project commits to from day one are documented in
`CAREMATE_MASTER_SPEC.md` section 9. AI (Gemini) is not used as a diagnostic
authority anywhere in this project; see section 10.
