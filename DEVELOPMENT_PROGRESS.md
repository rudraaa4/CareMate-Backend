# CareMate Development Progress

Current Phase: 2

## Completed

- [x] Phase 0 - Repository foundation
- [x] Phase 1 - FastAPI foundation
- [x] Phase 2 - PostgreSQL / SQLAlchemy / Alembic

## Current

- [ ] Phase 3 - User registration and authentication

### Current Tasks

- [ ] Create User model
- [ ] Create migration for users table
- [ ] Create UserCreate schema
- [ ] Add password hashing
- [ ] Implement POST /api/auth/register
- [ ] Reject duplicate email
- [ ] Implement POST /api/auth/login
- [ ] Generate access JWT
- [ ] Create authentication dependency
- [ ] Add GET /api/users/me
- [ ] Test invalid password / invalid token / missing token

## Not Started

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
- Local PostgreSQL 18 (already installed) is used for development. The app
  connects as a dedicated `caremate_user` role (not the `postgres`
  superuser) — least privilege, and matches how a real deployment would be
  configured. Credentials live only in `backend/.env` (git-ignored); see
  `.env.example` for the shape.
- Found and dropped a leftover `caremate` Postgres database (1 stray `users`
  table) from the same old prototype, at the user's request, and created a
  fresh empty one owned by `caremate_user` so Alembic migrations are the
  only thing that ever defines our schema.
- `alembic.ini` intentionally does not contain `sqlalchemy.url` — it's
  injected at runtime in `alembic/env.py` from `app.core.config.settings`,
  so the DB URL/credentials are never duplicated into a version-controlled
  file.

## Known Issues

None yet.

## Next Session

Begin Phase 3 - User Registration and Authentication: create the `User`
SQLAlchemy model (`app/models/user.py`), generate its Alembic migration,
add `UserCreate`/`UserResponse` Pydantic schemas, password hashing, and
`POST /api/auth/register`, `POST /api/auth/login` (JWT), and a protected
`GET /api/users/me` endpoint.
