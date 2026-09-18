# CareMate Development Progress

Current Phase: 3

## Completed

- [x] Phase 0 - Repository foundation
- [x] Phase 1 - FastAPI foundation
- [x] Phase 2 - PostgreSQL / SQLAlchemy / Alembic
- [x] Phase 3 - User registration and authentication

## Current

- [ ] Phase 4 - Patient profile

### Current Tasks

- [ ] Create PatientProfile model (one-to-one with User)
- [ ] Create schemas
- [ ] Create profile routes: GET /api/v1/profile, PUT/PATCH /api/v1/profile
- [ ] Decide: profile created during registration, or separately?
- [ ] Add ownership protection (a user can only touch their own profile)
- [ ] Test profile retrieval/update

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
- Password hashing: **bcrypt** (direct `bcrypt` package), not `passlib` —
  passlib is effectively unmaintained and has known compatibility breaks
  with recent bcrypt releases. JWT: **PyJWT**, not `python-jose` — more
  actively maintained.
- No service/repository layer yet — auth logic lives directly in
  `app/api/routes/auth.py`. Will introduce a service layer once logic gets
  genuinely complex (e.g. Phase 8 adherence calculations), not before.
- New routes use an `/api/v1/...` prefix per the spec's API design
  principles (section 14); `/api/health` stays unversioned as an infra
  endpoint, not a versioned business resource.
- `User.role` is a Postgres enum (currently only `patient`) via
  SQLAlchemy's `Enum(..., values_callable=...)` — without
  `values_callable`, SQLAlchemy stores the Python enum's *member name*
  ("PATIENT") instead of its *value* ("patient"); caught and fixed before
  the migration was applied.
- Tests run against a separate `caremate_test` Postgres database (created
  alongside `caremate`), never the dev database — wired via FastAPI's
  `app.dependency_overrides` in `tests/conftest.py`, with tables created/
  dropped once per test session and rows cleared between tests.

## Known Issues

None yet.

## Next Session

Begin Phase 4 - Patient Profile: create the `PatientProfile` SQLAlchemy
model with a one-to-one relationship to `User`, generate its migration,
add schemas and `GET`/`PUT` (or `PATCH`) `/api/v1/profile` routes, and
ensure a user can only ever read/write their own profile (via
`get_current_user`, the same pattern introduced in Phase 3).
