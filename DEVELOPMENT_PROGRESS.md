# CareMate Development Progress

Current Phase: 7

## Completed

- [x] Phase 0 - Repository foundation
- [x] Phase 1 - FastAPI foundation
- [x] Phase 2 - PostgreSQL / SQLAlchemy / Alembic
- [x] Phase 3 - User registration and authentication
- [x] Phase 4 - Patient profile
- [x] Phase 5 - Medicine management
- [x] Phase 6 - Medication scheduling
- [x] Phase 7 - Medication events

## Current

- [ ] Phase 8 - Adherence engine

### Current Tasks

- [ ] AdherenceService (first real service-layer module in the project)
- [ ] Document the adherence formula explicitly (e.g. taken / eligible_expected_doses * 100)
- [ ] Decide and document how SKIPPED/DELAYED/MISSED each count toward the formula
- [ ] get_daily_summary() / get_weekly_summary()
- [ ] Tests with known event fixtures producing predictable results

## Not Started

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
- `PatientProfile` is auto-created (empty) in the same DB transaction as
  `User`, via `db.flush()` to get the new user's id before `db.commit()`.
  Every user has exactly one profile from registration onward — enforced
  by a unique constraint on `patient_profiles.user_id`, not just app logic.
- `GET/PATCH /api/v1/profile` take no ID in the URL at all — "my profile"
  is derived entirely from the JWT via `get_current_user`. Structurally
  stronger than a runtime ownership check, since there's no ID a client
  could substitute to reach another user's profile.
- Added a dev-only test page (`tools/api-tester.html`, outside `backend/`
  and `frontend/`) plus CORS support in `app/main.py`
  (`Settings.cors_origins`) so it can call the API from a different port.
- `Medicine.patient_id` references `patient_profiles.id` (not `users.id`
  directly) — matches the spec's data model: User -> PatientProfile ->
  Medicine. `MedicineCreate`/`Update` schemas deliberately have no
  `patient_id` field; it's always derived server-side from
  `current_user.patient_profile.id` (spec section 9, rule 1).
- Cross-patient access returns **404**, not 403, on
  `GET/PATCH/DELETE /medicines/{id}` — a 403 would confirm the resource
  exists, leaking information about another patient's data. 404 makes
  "doesn't exist" and "exists but isn't yours" indistinguishable.
- Ownership check factored into one `get_owned_medicine` dependency
  (`app/api/routes/medicines.py`) reused by GET-one/PATCH/DELETE — the
  pattern every future owned-resource (schedules, events, documents) will
  repeat.
- `DELETE /medicines/{id}` soft-deletes (`active = False`), returns the
  updated resource (200, not 204) — history is needed later
  (adherence/timeline), so nothing is actually removed from the DB.
- `MedicationSchedule` has no `patient_id` of its own — one row per
  time-of-day (e.g. Metformin 08:00 and 20:00 are two rows sharing one
  `medicine_id`), `frequency` is an enum with only `DAILY` defined so far
  (spec: don't over-engineer recurrence yet). Ownership flows through the
  parent medicine: `POST/GET .../schedules` reuse Phase 5's
  `get_owned_medicine`; `PATCH/DELETE /schedules/{id}` use a new
  `get_owned_schedule` dependency that SQL-joins schedule -> medicine to
  check `patient_id`, since the schedule table has nothing to filter on
  directly.
- **Event generation is lazy, not cron/background-driven** (no scheduler
  exists yet — deliberately deferred to Phase 24 per the spec). Every call
  to `GET /medication-events/today` ensures today's events exist for all
  active schedules first (idempotent — DB unique constraint on
  `(schedule_id, scheduled_at)` backs this up, not just app logic), then
  returns them.
- **Status semantics, explicitly decided and documented in
  `app/api/routes/medication_events.py`:**
  `TAKEN`/`DELAYED`/`SKIPPED` are patient-confirmed and terminal — once
  set, `PATCH .../status` refuses further changes (409). `UPCOMING` and
  `MISSED` are system-inferred and never terminal. Marking taken always
  uses server time for `actual_taken_at` (never client-supplied); more
  than `DELAYED_THRESHOLD` (30 min) late becomes `DELAYED` instead of
  `TAKEN`, automatically — not something the client chooses directly. An
  `UPCOMING` event more than `MISSED_THRESHOLD` (2h) past its scheduled
  time flips to `MISSED` lazily, the next time it's read. `MISSED` can
  still transition to `TAKEN`/`DELAYED`/`SKIPPED` (a late dose should
  still be logged), unlike the three terminal states.
- **Timezone simplification:** `_local_now()` in
  `app/api/routes/medication_events.py` uses the server's local timezone
  for all "today"/"now" calculations — assumes every patient is in the
  same timezone. The spec (section 16) explicitly flags this as something
  not to assume forever; revisit when/if CareMate supports patients
  across timezones. Not needed yet for a single-region prototype.

## Known Issues

- **Port 8000 is currently unreliable in this Windows dev session** —
  after repeated server restarts during development, the OS was left with
  a stale/ambiguous listening-socket state on port 8000 that silently
  served responses from a dead process (missing recent routes) instead of
  the freshly started one. `netstat`/`Get-NetTCPConnection` output should
  not be trusted as ground truth while this persists — verify with
  `curl http://127.0.0.1:<port>/openapi.json` after any restart instead.
  Worked around by running the dev server on **port 8001** for the rest
  of this session (`tools/api-tester.html` defaults to 8001 accordingly).
  This is host/session state, not a code or project issue — likely
  resolves after a machine restart, at which point 8000 can be used again.

## Next Session

Begin Phase 8 - Adherence Engine: turn MedicationEvent history into
deterministic adherence metrics (expected/taken/missed/skipped/delayed
doses, adherence percentage, daily/weekly summaries). This is the
project's first genuinely "substantial" business logic — introduce a real
service layer here (`app/services/adherence_service.py`), as previously
decided in Phase 3's notes. Must explicitly document the formula and how
each status counts (e.g. does DELAYED count as adherent? Does SKIPPED
count differently from MISSED?) before implementing — the spec is
explicit that this must not be a silent decision.
