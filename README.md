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
- Pydantic / pydantic-settings (validation/schemas/config)
- PostgreSQL
- bcrypt (password hashing) + PyJWT (stateless access tokens)
- pytest (93 tests, run against an isolated test database)
- Git/GitHub for version control
- React (planned, later phase) for the frontend

## Current Implemented Features

Phases 0–12 of [`CAREMATE_MASTER_SPEC.md`](./CAREMATE_MASTER_SPEC.md) are
complete — see [`DEVELOPMENT_PROGRESS.md`](./DEVELOPMENT_PROGRESS.md) for
live, phase-by-phase status and the design decisions behind each one.

- **Auth**: registration, login (JWT via FastAPI's OAuth2 password flow),
  bcrypt password hashing, protected routes
- **Patient profile**: auto-created on registration, editable
- **Medicines**: full CRUD, soft-archive, strictly scoped per patient
- **Schedules**: one or more times per day per medicine
- **Medication events**: today's doses generated on demand, mark
  taken/skipped, automatic MISSED/DELAYED classification
- **Adherence**: a real percentage computed from event history, not guessed
- **Inventory**: stock tracking with exactly-once decrement on a taken dose,
  low-stock/days-remaining estimates
- **Dashboard**: one endpoint aggregating all of the above
- **Health notes**: free-form patient observations, optionally tied to a
  medicine
- **Medical documents**: secure upload/list/download (PDF/JPEG/PNG), with
  server-generated storage keys (no path traversal via filenames) and no
  static file exposure

Every resource above enforces strict per-patient ownership — cross-patient
access is explicitly tested for each one (see `backend/tests/`).

## Local Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows; use `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt

cp ../.env.example .env      # then fill in DATABASE_URL and SECRET_KEY
alembic upgrade head

uvicorn app.main:app --reload
```

## Environment Variables

See [`.env.example`](./.env.example) for the current list of expected
environment variables. Never commit a real `.env` file — it is git-ignored.

## Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "description of the change"
alembic upgrade head
```

The database URL is read from `Settings` (`.env`), not hardcoded in
`alembic.ini` — credentials are never duplicated into a version-controlled
file.

## Tests

```bash
cd backend
venv\Scripts\activate
pytest -v
```

Tests run against a separate `caremate_test` database and a temp file-storage
directory — they never touch dev data or write real files into
`backend/uploads/`.

## API Documentation

With the server running, interactive docs are available at
`http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc`.

## Project Roadmap

See [`CAREMATE_MASTER_SPEC.md`](./CAREMATE_MASTER_SPEC.md) sections 11 and 12
for the full phase list and milestone groupings (Milestone A: FastAPI Core →
Milestone G: Productization).

## Safety / Privacy Limitations

CareMate handles health-related information. Only fictional/dev-test data has
ever been stored in any environment tied to this repository — no real patient
data. Security principles the project commits to from day one are documented
in `CAREMATE_MASTER_SPEC.md` section 9 (patient-ID ownership enforced
server-side everywhere, passwords never stored in plaintext, uploaded files
never exposed through unrestricted public paths). AI (Gemini) is not used
anywhere in this project yet — no AI phase has been reached — and per section
10, it will never be a diagnostic authority when it is introduced.

Known, documented limitations (not yet addressed): inventory decrement isn't
safe under a true concurrent race; uploaded file type is validated by
declared content-type, not by inspecting file bytes; date/time logic assumes
a single server timezone. See `DEVELOPMENT_PROGRESS.md` for the full list and
reasoning behind each.
