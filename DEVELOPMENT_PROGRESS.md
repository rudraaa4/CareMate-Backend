# CareMate Development Progress

Current Phase: 12

## Completed

- [x] Phase 0 - Repository foundation
- [x] Phase 1 - FastAPI foundation
- [x] Phase 2 - PostgreSQL / SQLAlchemy / Alembic
- [x] Phase 3 - User registration and authentication
- [x] Phase 4 - Patient profile
- [x] Phase 5 - Medicine management
- [x] Phase 6 - Medication scheduling
- [x] Phase 7 - Medication events
- [x] Phase 8 - Adherence engine
- [x] Phase 9 - Medicine inventory
- [x] Phase 10 - Patient dashboard
- [x] Phase 11 - Health notes
- [x] Phase 12 - Medical document vault

**MILESTONE B - Working Medication Tracker (Phases 5-10) complete.**
Medicine -> Schedule -> Event -> Adherence -> Inventory -> Dashboard all
exist and are wired together. Per the spec: "At this point CareMate is
already a functioning backend product."

## Current

- [ ] Phase 13 - Prescription Domain Model

### Current Tasks

- [ ] Prescription model (patient_id, document_id optional, doctor_name, hospital_name, prescription_date, notes, source)
- [ ] CRUD scoped to patient, ownership-checked
- [ ] Optional link to a MedicalDocument (the uploaded prescription file, if any)
- [ ] Distinguish prescription-as-domain-object from generic document metadata

## Not Started

- [ ] Phases 13+ - see CAREMATE_MASTER_SPEC.md (Milestone C continued: Prescriptions -> Timeline)

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
- **Timezone simplification:** `local_now()` (`app/core/timezone.py`) uses
  the server's local timezone for all "today"/"now" calculations —
  assumes every patient is in the same timezone. The spec (section 16)
  explicitly flags this as something not to assume forever; revisit
  when/if CareMate supports patients across timezones. Not needed yet for
  a single-region prototype.
- **Phase 8 refactor:** promoted the Phase 7 status logic (missed
  detection, event generation, delayed classification) out of
  `app/api/routes/medication_events.py` and into
  `app/services/medication_event_service.py`. This wasn't optional
  cleanup — `AdherenceService` needs the exact same "is this event really
  MISSED" rule the HTTP routes use, even for events nobody has fetched
  over the API yet (so their status is still stale `UPCOMING` in the DB).
  Needing identical logic in two places was the signal to promote it.
  `app/core/timezone.py` (`local_now()`) was factored out the same way,
  for the same reason (previously duplicated as a private function).
- **Adherence formula, decided and documented explicitly in
  `app/services/adherence_service.py`:**
  `adherence % = taken / eligible_expected_doses * 100`. `UPCOMING`
  events are excluded (not due yet). `DELAYED` counts as taken (the dose
  *was* taken; lateness is a separate signal, tracked for Phase 28, not
  this phase). `MISSED` and `SKIPPED` both count as eligible-but-not-taken
  (correctly reduce the percentage) but are reported as separate counts
  so the distinction between "passive" and "deliberate" non-adherence
  isn't lost. Zero eligible doses yields `adherence_percentage = None`,
  not 0 or 100 — a brand-new patient has no adherence data, which is
  different from having failed or succeeded.
- **No HTTP endpoint this phase, deliberately** — the spec's Phase 8
  section has no "APIs" heading, only a service + a test-driven
  Definition of Done. Adherence gets exposed over HTTP starting Phase 10
  (dashboard). Verified via `pytest` only this phase, not the tester tool.
- **Inventory is opt-in per medicine, not auto-created.** Unlike
  `PatientProfile` (every user gets one automatically — there's no
  meaningful "no profile" state), an auto-created empty inventory would
  immediately show "0 remaining, low stock" for every medicine, which is
  noise, not help. `POST /medicines/{id}/inventory` sets it up explicitly
  with real starting numbers; `GET`/`PATCH` 404 until that's done.
- **Double-decrement guard, and its honest limit:** inventory only
  decrements inside `medication_event_service.mark_taken()`, called only
  from the branch of `update_event_status` that's unreachable once an
  event is already `TAKEN`/`DELAYED`/`SKIPPED` (Phase 7's terminal-status
  409 guard) — so under normal sequential use, a given event can decrement
  at most once, verified by a test that PATCHes taken twice and checks
  quantity only dropped once. **Not fully closed:** a true concurrent race
  (two simultaneous requests both reading "not yet terminal" before either
  commits) isn't defended against — that needs row-level locking
  (`SELECT ... FOR UPDATE`) or an optimistic-concurrency version column,
  which is Phase 32 hardening, not asked for here. Documented rather than
  silently left as a gap.
- `estimated_days_remaining` divides doses-remaining by the count of
  *active* schedules for the medicine (each = 1 dose/day, since Phase 6
  only supports `DAILY` frequency so far) — `None` when there's no active
  schedule to divide by, rather than a division-by-zero or a misleading 0.
- Decrementing clamps `current_quantity` at 0 (never negative) — logging
  more doses than physically remained shouldn't produce a confusing
  negative stock count.
- **Phase 10 dashboard's `adherence_percentage` is a 7-day rolling window
  (`AdherenceService.get_weekly_summary()`), not literally today's.** A
  same-day figure looks artificially perfect early in the day (doses not
  yet due aren't "eligible," so 3-of-3-taken-so-far shows 100% even with
  1 more due later) — a trailing week is a more honest headline number.
- **Phase 10 refactor:** extracted `get_or_create_todays_events()` into
  `medication_event_service.py` (previously inline in the
  `GET /medication-events/today` route) specifically so the dashboard
  could reuse the identical query instead of duplicating it — directly
  required by this phase's own Definition of Done ("without duplicating
  business logic"). Verified behavior-preserving: all 63 pre-existing
  tests still passed immediately after, before any dashboard code was
  added.
- **`today.scheduled` can exceed `today.taken + today.remaining`** — the
  gap is `MISSED`/`SKIPPED` doses, which aren't broken out as their own
  top-level field (matching the spec's minimal 3-field example response).
  Confirmed correct, not a bug, via manual testing: a genuinely overdue
  schedule showed `scheduled:1, taken:0, remaining:0` before being
  addressed.
- `active_medicines` is a plain inline count query in the route, not a
  service method — a one-line count isn't business logic worth
  abstracting; only the adherence/inventory/event aggregation reuses
  services.
- **Phase 11 hard-deletes, unlike every prior resource.**
  `DELETE /health-notes/{id}` really removes the row (204, verified by a
  subsequent GET returning 404) rather than soft-archiving like
  `Medicine`/`MedicationSchedule` do. Deliberate: a personal note carries
  no adherence/timeline history that needs preserving, and a patient
  should be able to actually remove something they wrote.
- **`medicine_id` on a health note is validated for ownership at the
  application layer, not just the DB FK.** It arrives inside the request
  body (not the URL), so a client could try to tag a note with another
  patient's medicine ID; the FK alone would only reject a genuinely
  nonexistent ID, not one that exists but belongs to someone else. Rejected
  with `400` (invalid request value) rather than `404` (reserved for the
  primary resource in the URL — the note itself). Verified manually:
  Patient B tagging a note with Patient A's medicine_id -> 400.
- `recorded_at` is client-settable (defaults to now if omitted) — unlike
  `MedicationEvent.actual_taken_at` (always server time, Phase 7, to
  prevent spoofing when adherence math depends on it), a health note's
  timing is inherently the patient's own account of when something
  happened, not something to guard against.
- **Phase 12 storage is a `FileStorage` interface + `LocalFileStorage`**
  (`app/storage/`), injected via a `get_storage` FastAPI dependency —
  same reasoning as `get_db`: tests override it with a temp directory
  (`tests/conftest.py`), so they never write real files into
  `backend/uploads/`. Swapping local disk for real object storage later
  is one new class, not a rewrite of every route.
- **The actual path-traversal defense is that `storage_key` is always
  server-generated** (`uuid4().hex` + an extension pulled from a
  whitelist keyed by declared content-type — never the client's claimed
  filename or extension). `original_filename` is stored only as display
  metadata and never used to build a filesystem path. Verified with a
  test uploading a file literally named `../../../../etc/passwd` — it
  uploads and downloads correctly, with that string preserved harmlessly
  as metadata. `LocalFileStorage` also has a resolve-and-contain check as
  defense in depth, though it's not the primary defense.
- **Content-type validation is declared-type + whitelist, not file-magic
  inspection.** We trust the client-reported content type against
  `ALLOWED_CONTENT_TYPES` (PDF/JPEG/PNG); we don't verify the actual file
  bytes match (that needs a library like `python-magic` and is real
  hardening, not something this phase's spec asks for) — same category of
  honestly-documented limitation as Phase 9's concurrency note.
- **Uploads are never statically mounted** — no `StaticFiles` on
  `backend/uploads/`. The only way to retrieve file bytes is
  `GET /documents/{id}/download`, authenticated and ownership-checked.
  Verified by a test hitting `/uploads/anything.pdf` directly and
  confirming 404.
- **Scope: no PATCH/DELETE for documents this phase**, unlike Phase 11's
  notes. The spec's Phase 12 Definition of Done says "upload/list/
  retrieve" only, unlike Phase 11's which explicitly said "edit/delete."
  Deferred rather than added preemptively — can be added on request.
- Size limit (`Settings.max_upload_size_bytes`, default 10 MB) is
  enforced by reading the upload in 1 MB chunks and aborting as soon as
  the running total exceeds the cap, before ever writing to storage —
  bounds how much a client can force the server to buffer, regardless of
  what size it actually claims to be sending.

## Known Issues

- **Stale/ghost-listener port syndrome has now affected 8000, 8001, and
  8002 across this Windows session — it recurs on essentially any port
  reused enough times in one session, not something tied to a specific
  port number.** Symptom each time: a freshly restarted server is
  missing recently-added routes; `Get-NetTCPConnection` keeps reporting a
  listener even after killing every matching process by real Windows
  PID. Confirmed every time that the *application* is correct via a
  direct in-process check (`python -c "from app.main import app;
  app.openapi()"`, bypassing uvicorn entirely) before concluding it's the
  OS, not the code. **Currently on port 8003** (`tools/api-tester.html`
  updated accordingly). Given the pattern across four ports now, treat
  any recurrence as confirmation this needs a machine restart — stop
  troubleshooting it and just bump the port again, noting it here.
  `netstat`/`Get-NetTCPConnection` should not be trusted as ground truth
  for "what's actually being served" while this persists; verify with
  `curl http://127.0.0.1:<port>/openapi.json` (or the in-process check
  above) after any restart instead.

## Next Session

Begin Phase 13 - Prescription Domain Model: treat prescriptions as
healthcare domain objects, not only generic uploaded files. `Prescription`
model (patient_id, optional document_id linking to an uploaded
`MedicalDocument`, doctor_name, hospital_name, prescription_date, notes,
source). CRUD scoped to patient. Later phases (16: AI extraction, 20:
structured digital prescriptions) build on this, but don't implement
those yet — this phase is just the domain object and basic CRUD.
