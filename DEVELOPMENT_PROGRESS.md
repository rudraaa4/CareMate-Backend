# CareMate Development Progress

Current Phase: 1

## Completed

- [x] Phase 0 - Repository foundation
- [x] Phase 1 - FastAPI foundation

## Current

- [ ] Phase 2 - PostgreSQL / SQLAlchemy / Alembic

### Current Tasks

- [ ] Install PostgreSQL locally / configure dev instance
- [ ] Create CareMate database
- [ ] Configure DATABASE_URL via environment variables
- [ ] Create app/core/config.py
- [ ] Configure SQLAlchemy engine/session
- [ ] Add get_db dependency
- [ ] Configure declarative model base
- [ ] Introduce Alembic
- [ ] Verify migrations run

## Not Started

- [ ] Phase 3 - User registration and authentication
- [ ] Phase 3 - User registration and authentication
- [ ] Phase 4 - Patient profile
- [ ] Phase 5 - Medicine management
- [ ] Phase 6 - Medication scheduling
- [ ] Phase 7 - Medication events
- [ ] Phase 8 - Adherence engine
- [ ] Phase 9 - Medicine inventory
- [ ] Phase 10 - Patient dashboard
- [ ] Phases 11+ - see CAREMATE_MASTER_SPEC.md

## Decisions

- Dependency management: **requirements.txt** (not Poetry/pyproject.toml) — simplest
  mental model while learning FastAPI; only one file to understand, no extra
  packaging concepts. Can migrate to pyproject.toml later if needed.
- Project root: `C:\Users\Rudra\CareMate`, backend code lives under `backend/`
  so a `frontend/` directory can sit alongside it later without restructuring.
- Package structure inside `backend/app/` will follow the master spec's
  feature-based layout (`core/`, `models/`, `schemas/`, `api/routes/`, etc.),
  introduced incrementally — we do not create empty placeholder folders before
  they hold real code.
- Deleted an unrelated pre-existing prototype at
  `C:\Users\Rudra\.gemini\antigravity-ide\scratch\caremate-backend`
  (built earlier with a different tool, further along than our Phase 0/1 but
  not following the phased spec) at the user's request, since it was
  occupying port 8000 and unrelated to this repository.

## Known Issues

None yet.

## Next Session

Begin Phase 2 - PostgreSQL, SQLAlchemy and Alembic: install/configure a local
PostgreSQL instance, create the `caremate` database, add `app/core/config.py`
and `app/core/database.py` (engine, session, `get_db` dependency, declarative
base), then introduce Alembic and verify migrations run.
