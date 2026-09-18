# CareMate Master Build Specification

## 1. Purpose of This File

This document is the authoritative engineering specification and development roadmap for CareMate.

CareMate is an AI-assisted continuity-of-care platform. It is NOT merely a medicine reminder application. The product is designed to connect what a clinician prescribed with what actually happens afterward, while keeping the patient in control of their information.

This specification describes the complete long-term architecture so that a coding agent such as Claude Code or Codex understands where the project is going.

IMPORTANT: The complete vision must NOT be implemented at once.

The project must be built sequentially, phase by phase. Each phase must leave the application in a working, testable state.

---

# 2. Core Product Vision

Healthcare often becomes fragmented after a patient leaves a hospital or clinic.

A doctor knows what was prescribed, but between appointments:

- medicines may be missed or delayed
- prescriptions may be lost
- reports may be scattered across paper files, messages, hospital portals, and phone galleries
- medicine stock may run out
- family members may lack useful visibility
- clinicians may have limited information about what actually happened after the prescription

CareMate aims to create a continuous patient-controlled care journey:

Doctor -> Prescription -> Patient at Home -> Medication Adherence -> Inventory -> Medical Records -> Caregiver Context -> Follow-up -> Doctor

Core positioning:

"The prescription was only the beginning."

"The missing link between prescription and progress."

CareMate should eventually connect:

- Patient
- Family / Caregiver
- Doctor
- Hospital
- Prescriptions
- Medicines
- Medication schedules
- Medication events
- Adherence
- Inventory
- Medical documents
- Treatment history
- AI-assisted understanding

Gemini is an intelligence layer inside CareMate, not the product itself.

---

# 3. Development Philosophy

The primary developer is learning FastAPI while building CareMate.

The codebase must therefore satisfy BOTH requirements:

1. Be reasonably production-oriented.
2. Remain understandable enough that the developer can explain it in an interview.

Prefer clear Python over clever Python.

Do not introduce abstractions merely because they are common in large enterprise projects.

When introducing an important concept, explain why CareMate needs it.

Examples:

- dependency injection
- SQLAlchemy sessions
- ORM relationships
- Pydantic schemas
- JWT
- OAuth2PasswordBearer
- async/await
- middleware
- background tasks
- Alembic
- repositories
- service layer
- file storage
- vector databases
- RAG
- caching

The developer should understand the request flow:

Client
  -> Router
  -> Service
  -> Repository / ORM
  -> PostgreSQL
  -> Response Schema

---

# 4. Mandatory Coding-Agent Rules

These rules apply whenever an AI coding agent works on this repository.

## 4.1 Never Build Everything at Once

This document describes the COMPLETE CareMate vision.

DO NOT implement the complete specification in one pass.

Work sequentially through the phases defined later.

## 4.2 Before Every Phase

The coding agent must:

1. Read this file.
2. Read DEVELOPMENT_PROGRESS.md.
3. Inspect the existing repository.
4. Identify the current unfinished phase.
5. Explain what the phase accomplishes.
6. Explain important concepts being introduced.
7. List files expected to be created or modified.
8. Identify database changes.
9. Identify API changes.
10. Wait for developer approval before making substantial changes if requested.

## 4.3 During Implementation

The coding agent must:

- implement only the current phase
- preserve already-working functionality
- avoid unrelated refactoring
- avoid introducing future features prematurely
- use environment variables for secrets
- add validation
- add useful error handling
- preserve patient ownership boundaries
- add/update tests
- run relevant tests and commands
- fix errors caused by the implementation

## 4.4 After Every Phase

The coding agent must:

1. Run tests.
2. Verify the application starts where applicable.
3. Explain every important file created or modified.
4. Explain the request/data flow.
5. State known limitations.
6. Update DEVELOPMENT_PROGRESS.md.
7. Mark the phase complete only if its Definition of Done is satisfied.
8. STOP before beginning the next phase.

## 4.5 Learning Rule

When generating unfamiliar code, explain:

WHAT it does.
WHY CareMate needs it.
WHERE it belongs.
HOW data flows through it.
HOW to test it.

Never hide important behavior behind unexplained boilerplate.

---

# 5. Proposed Technology Stack

## Backend

- Python 3.12+ where compatible
- FastAPI
- Uvicorn
- Pydantic
- SQLAlchemy 2.x
- PostgreSQL
- Alembic
- psycopg
- python-jose or another maintained JWT solution selected at implementation time
- passlib/bcrypt or an appropriate maintained password hashing stack
- python-multipart for uploads where required
- pytest
- httpx / FastAPI TestClient as appropriate

Choose current maintained libraries when implementation begins. Do not blindly add every dependency listed here.

## AI

- Google Gemini API
- Structured JSON outputs where appropriate
- RAG only after the ordinary application and medical-document pipeline work

## Frontend

Planned:

- React
- JavaScript or TypeScript, decide before frontend phase
- REST API integration

The backend must work independently before the frontend becomes a dependency.

## Infrastructure Later

- Docker
- PostgreSQL production instance
- object/file storage
- HTTPS
- CI/CD
- logging/monitoring
- backups

---

# 6. Target Repository Structure

The structure may evolve, but prefer something understandable like:

CareMate/
|
|-- README.md
|-- CAREMATE_MASTER_SPEC.md
|-- DEVELOPMENT_PROGRESS.md
|-- .gitignore
|-- .env.example
|
|-- backend/
|   |-- requirements.txt or pyproject.toml
|   |-- alembic.ini
|   |
|   |-- app/
|   |   |-- main.py
|   |   |
|   |   |-- core/
|   |   |   |-- config.py
|   |   |   |-- database.py
|   |   |   `-- security.py
|   |   |
|   |   |-- models/
|   |   |-- schemas/
|   |   |-- repositories/
|   |   |-- services/
|   |   |-- api/
|   |   |   |-- dependencies.py
|   |   |   `-- routes/
|   |   |
|   |   |-- ai/
|   |   |-- storage/
|   |   |-- utils/
|   |   `-- exceptions/
|   |
|   |-- alembic/
|   `-- tests/
|
|-- frontend/
|
`-- docs/

Do not create empty directories merely to imitate this structure. Introduce them when they become useful.

---

# 7. Architectural Responsibilities

## Router

Responsible for HTTP concerns:

- route path
- request parsing
- dependencies
- status codes
- response schemas

Routers should not contain large amounts of business logic.

## Schema

Pydantic schemas define validated API input/output.

Examples:

MedicineCreate
MedicineUpdate
MedicineResponse

Do not expose ORM objects blindly.

## Model

SQLAlchemy models represent persistent database entities.

## Service

Business logic belongs here when it is substantial.

Examples:

- calculating adherence
- marking a medication event taken
- validating patient ownership
- reducing inventory
- generating dashboard summaries

## Repository

Optional abstraction for database operations.

Do not force a repository layer into every trivial feature if it makes the beginner code harder to understand. If introduced, use it consistently and explain why.

## Dependency

FastAPI dependencies handle reusable request-time concerns such as:

- database session
- authenticated user
- authorization checks

## AI Layer

AI calls must be isolated from ordinary domain logic.

The application should remain useful when Gemini is temporarily unavailable.

---

# 8. Core Data Model Vision

Do NOT create all these tables immediately.

They represent the long-term direction.

User
 |
 +-- PatientProfile
 |      |
 |      +-- Medicine
 |      |      |
 |      |      +-- MedicationSchedule
 |      |      |        |
 |      |      |        +-- MedicationEvent
 |      |      |
 |      |      +-- MedicineInventory
 |      |
 |      +-- MedicalDocument
 |      +-- Prescription
 |      +-- HealthNote
 |      +-- CaregiverRelationship
 |      +-- DoctorPatientAccess
 |
 +-- Caregiver-related identity/role
 |
 +-- DoctorProfile
        |
        +-- Hospital / HospitalMembership
        +-- Visit

Additional tables may later include:

- Consent
- Notification
- AuditLog
- PrescriptionItem
- AIExtractionDraft
- RefreshToken/session information
- Timeline-related domain entities if necessary

---

# 9. Security Principles From Day One

CareMate handles health-related information. Security cannot be bolted on at the end.

Core rules:

1. Never trust a patient_id supplied by the client when the authenticated user determines the patient.
2. Every patient-owned resource must enforce ownership.
3. Patient A must never retrieve Patient B's medicine, event, document, prescription, or inventory.
4. Passwords are never stored in plaintext.
5. Secrets are never committed to Git.
6. Uploaded files are not exposed through unrestricted public paths.
7. Doctor and caregiver access must be explicit and permission-based.
8. AI receives only the context the authenticated actor is authorized to access.
9. Log access to sensitive resources when the audit phase is introduced.
10. Avoid including sensitive information in application logs.

---

# 10. AI Safety / Product Rules

Gemini may help:

- extract structured information from prescriptions
- understand medical documents
- organize records
- summarize existing patient history
- explain adherence patterns
- answer questions grounded in authorized CareMate records

Gemini must NOT be treated as:

- a physician
- a diagnostic authority
- an autonomous medication prescriber
- a trusted source for drug interactions without verified external data

Important workflow:

Prescription
  -> AI extraction
  -> structured DRAFT
  -> validation
  -> patient/authorized clinician confirmation
  -> CareMate records

Never:

Prescription
  -> AI guess
  -> automatically activate medication dosage

Deterministic tasks such as inventory arithmetic and database retrieval should not be delegated to an LLM.

---

# 11. DEVELOPMENT PHASES

# PHASE 0 - Repository and Specification Foundation

## Goal

Create a clean project foundation before application development.

## Steps

1. Initialize Git repository.
2. Add this master specification.
3. Create DEVELOPMENT_PROGRESS.md.
4. Add README.
5. Add .gitignore.
6. Add .env.example.
7. Create backend directory.
8. Decide dependency management approach.
9. Document local development commands.

## Definition of Done

- repository starts cleanly
- secrets are ignored
- master spec exists
- progress file exists
- developer understands project structure

---

# PHASE 1 - FastAPI Foundation

## Goal

Create the smallest working CareMate API.

## Steps

1. Create virtual environment.
2. Install FastAPI and Uvicorn.
3. Create app/main.py.
4. Instantiate FastAPI.
5. Add GET /api/health.
6. Run using Uvicorn.
7. Test Swagger/OpenAPI.
8. Add first pytest test.

Example response:

{
  "status": "UP",
  "service": "CareMate API"
}

## Concepts to Learn

- FastAPI app
- decorators
- route functions
- request/response
- Swagger
- Uvicorn
- virtual environments

## Definition of Done

- server runs
- /api/health returns 200
- Swagger opens
- test passes

---

# PHASE 2 - PostgreSQL, SQLAlchemy and Alembic

## Goal

Replace temporary/file-based persistence with a real relational database.

## Steps

1. Install PostgreSQL locally or configure development instance.
2. Create CareMate database.
3. Configure DATABASE_URL through environment variables.
4. Create config module.
5. Configure SQLAlchemy engine/session.
6. Add get_db dependency.
7. Configure declarative model base.
8. Introduce Alembic.
9. Create a minimal test model only if needed, otherwise coordinate with Phase 3.
10. Verify migrations.

## Concepts to Learn

- ORM
- engine
- session
- dependency injection
- migration
- environment variables
- transaction basics

## Definition of Done

- FastAPI connects to PostgreSQL
- Alembic can create/apply migrations
- database credentials are not committed
- database session lifecycle is understood

---

# PHASE 3 - User Registration and Authentication

## Goal

Create secure patient authentication.

## Initial Entities

User:
- id
- email
- password_hash
- role
- is_active
- created_at
- updated_at

Initially role may support PATIENT only while leaving room for future roles.

## Steps

1. Create User model.
2. Create migration.
3. Create UserCreate schema.
4. Create login schema if needed.
5. Add password hashing.
6. Implement registration.
7. Reject duplicate email.
8. Implement login.
9. Generate access JWT.
10. Create authentication dependency.
11. Protect a test endpoint.
12. Add GET /api/users/me or equivalent.
13. Test invalid password.
14. Test invalid/expired token.
15. Test protected route without token.

## Example APIs

POST /api/auth/register
POST /api/auth/login
GET /api/users/me

## Definition of Done

Register -> Login -> JWT -> Protected Endpoint works.

Passwords are hashed.

Authentication tests pass.

---

# PHASE 4 - Patient Profile

## Goal

Separate authentication identity from healthcare profile information.

## PatientProfile Fields

Initial version:

- id
- user_id
- full_name
- date_of_birth optional
- phone optional
- created_at
- updated_at

Avoid collecting unnecessary personal data.

## Steps

1. Create PatientProfile model.
2. Add one-to-one User relationship.
3. Create schemas.
4. Create profile service/routes.
5. Determine whether profile is created during registration or separately.
6. Add ownership protection.
7. Test profile retrieval/update.

## APIs

GET /api/profile
PUT/PATCH /api/profile

## Definition of Done

Authenticated patient can retrieve/update only their own profile.

---

# PHASE 5 - Medicine Management

## Goal

Allow a patient to maintain their current medication list.

## Medicine Fields

Initial:

- id
- patient_id
- name
- strength optional
- form optional
- instructions optional
- start_date optional
- end_date optional
- active
- created_at
- updated_at

## Schemas

MedicineCreate
MedicineUpdate
MedicineResponse

## APIs

POST /api/medicines
GET /api/medicines
GET /api/medicines/{medicine_id}
PATCH /api/medicines/{medicine_id}
DELETE or archive endpoint

Prefer soft archive/deactivation where history matters.

## Critical Security Test

Patient A creates Medicine 42.

Patient B requests Medicine 42.

Access must be denied or safely hidden.

## Definition of Done

Authenticated patients can CRUD/archive only their own medicines.

---

# PHASE 6 - Medication Scheduling

## Goal

Represent WHEN a medicine should be taken separately from WHAT the medicine is.

## MedicationSchedule Fields

Possible initial design:

- id
- medicine_id
- time_of_day
- frequency
- start_date
- end_date optional
- active
- created_at

Do not over-engineer recurrence initially.

## Example

Metformin 500 mg

Schedule:
08:00
20:00

## APIs

POST /api/medicines/{id}/schedules
GET /api/medicines/{id}/schedules
PATCH /api/schedules/{id}
Archive schedule

## Definition of Done

Patient can define and retrieve schedules for owned medicines.

---

# PHASE 7 - Medication Events

## Goal

Record what actually happens after a medicine is scheduled.

This is a core CareMate concept.

## MedicationEvent Fields

- id
- schedule_id
- scheduled_at
- status
- actual_taken_at optional
- note optional
- created_at
- updated_at

## Status

UPCOMING
TAKEN
MISSED
SKIPPED
DELAYED

Define status semantics explicitly.

## Steps

1. Create event model.
2. Decide event generation strategy.
3. Generate upcoming events safely.
4. Mark event TAKEN.
5. Store actual taken timestamp.
6. Support SKIPPED.
7. Determine when events become MISSED.
8. Prevent cross-patient event access.
9. Make state transitions explicit.

## APIs

GET /api/medication-events/today
PATCH /api/medication-events/{id}/status

Exact routes may evolve.

## Definition of Done

CareMate can distinguish prescribed schedule from actual medication behavior.

---

# PHASE 8 - Adherence Engine

## Goal

Turn medication events into useful deterministic adherence metrics.

## Initial Metrics

- expected doses
- taken doses
- missed doses
- skipped doses
- delayed doses
- adherence percentage
- adherence by time period

The exact formula must be documented.

Example starting formula:

taken / eligible_expected_doses * 100

Do not silently decide how skipped/delayed events count. Document the chosen semantics.

## Service

AdherenceService

Possible methods:

- calculate_period_adherence()
- get_daily_summary()
- get_weekly_summary()
- get_time_of_day_patterns()

## Definition of Done

Given known event fixtures, adherence calculations produce predictable tested results.

---

# PHASE 9 - Medicine Inventory

## Goal

Track medicine quantity and estimate when stock will run low.

## MedicineInventory

- id
- medicine_id
- current_quantity
- units_per_dose
- low_stock_threshold
- updated_at

## Logic

When an event becomes TAKEN:

MedicationEventService
  -> InventoryService
  -> decrement appropriate quantity

Avoid decrementing multiple times if a TAKEN event is edited repeatedly.

## Calculations

- current quantity
- estimated doses remaining
- estimated days remaining where calculable
- low stock boolean

Gemini is NOT needed.

## Definition of Done

Taking a dose changes inventory exactly once and low-stock calculations are tested.

---

# PHASE 10 - Patient Dashboard

## Goal

Aggregate current CareMate state into one useful API.

## Dashboard Data

Possible initial response:

{
  "today": {
    "scheduled": 4,
    "taken": 3,
    "remaining": 1
  },
  "adherence_percentage": 92.0,
  "low_stock_count": 1,
  "active_medicines": 3
}

## Data Sources

- Medicine
- MedicationSchedule
- MedicationEvent
- MedicineInventory
- AdherenceService

## Definition of Done

One authenticated endpoint gives a useful current patient summary without duplicating business logic.

---

# PHASE 11 - Health Notes

## Goal

Allow patients to attach simple observations to their care history.

Examples:

- nausea after evening dose
- headache
- feeling better
- note for next appointment

## Fields

- id
- patient_id
- text
- recorded_at
- optional medicine association
- created_at

Do not turn free-form notes into diagnoses.

## Definition of Done

Patient can create, retrieve, edit/delete as appropriate, and own their notes.

---

# PHASE 12 - Medical Document Vault

## Goal

Securely organize medical files.

## Document Types

PRESCRIPTION
LAB_REPORT
SCAN_REPORT
DISCHARGE_SUMMARY
DOCTOR_NOTE
OTHER

## MedicalDocument Fields

- id
- patient_id
- document_type
- storage_key/path
- original_filename
- content_type
- document_date optional
- description optional
- uploaded_at

## Steps

1. Implement upload validation.
2. Define allowed types/sizes.
3. Store files using a storage abstraction.
4. Store metadata in PostgreSQL.
5. Implement authorized download.
6. Prevent path traversal.
7. Do not expose raw unrestricted upload directory.
8. Test ownership.

Initially local development storage is acceptable if cleanly abstracted for later object storage.

## Definition of Done

Patient can securely upload/list/retrieve only their own supported documents.

---

# PHASE 13 - Prescription Domain Model

## Goal

Treat prescriptions as healthcare domain objects, not only generic files.

## Prescription

Possible fields:

- id
- patient_id
- document_id optional
- doctor_name optional
- hospital_name optional
- prescription_date
- notes optional
- source
- created_at

Later PrescriptionItem can hold structured medicines.

## Definition of Done

CareMate can store and list prescription history independently of generic document metadata.

---

# PHASE 14 - Medical Timeline / Care Thread

## Goal

Expose the patient's longitudinal care story.

The timeline represents the backend version of the Care Thread concept.

## Timeline Sources

- prescriptions
- document uploads
- treatment starts/changes
- health notes
- adherence summaries
- future visits

Avoid creating a giant timeline table unless domain requirements justify it.

Prefer an aggregation service that creates TimelineItem schemas.

## Example

JAN
- Consultation
- Prescription
- Treatment started

FEB
- Lab report
- Follow-up
- Prescription updated

MAR
- Treatment continued
- 92% adherence

## Definition of Done

GET /api/timeline returns ordered patient-authorized care events.

---

# PHASE 15 - Gemini Integration Foundation

## Goal

Introduce Gemini behind a dedicated service boundary.

Do NOT build a generic chatbot first.

## Structure

app/ai/
- gemini_client.py
- prompts/
- schemas/
- services/

## Rules

- API key from environment
- timeouts
- graceful failure
- structured output where possible
- log operational failures without leaking medical data
- AI unavailable must not break ordinary medication management

## Definition of Done

Backend can make a controlled test Gemini request through an isolated AI service.

---

# PHASE 16 - AI Prescription Extraction

## Goal

Convert uploaded prescriptions into reviewable structured drafts.

## Pipeline

Prescription upload
   -> Document stored
   -> Extraction request
   -> Gemini
   -> structured JSON
   -> Pydantic validation
   -> AIExtractionDraft
   -> patient review
   -> confirm/correct
   -> Medicine + Schedule creation

## Extracted Fields

Possible:

- medicine name
- strength
- form
- frequency
- instructions
- duration
- uncertain fields/confidence indicators where supported

## Safety Rule

AI extraction is DRAFT DATA.

Never automatically activate treatment because Gemini inferred it.

## Failure Cases

- unreadable document
- unsupported file
- malformed JSON
- incomplete medicine
- ambiguous dosage
- Gemini unavailable
- patient rejects extraction

## Definition of Done

Prescription -> structured draft -> patient confirmation -> CareMate records works with failure handling.

---

# PHASE 17 - Caregiver Accounts and Relationships

## Goal

Allow patient-authorized family/caregiver participation.

## Relationship

CaregiverRelationship:
- id
- patient_id
- caregiver_user_id
- status
- created_at
- revoked_at optional

Decide whether caregiver is a User role or separate profile while keeping authentication unified.

## Flow

Patient invites
 -> caregiver accepts
 -> patient selects permissions
 -> caregiver accesses only authorized data
 -> patient can revoke

## Definition of Done

Caregiver can access only explicitly permitted patient information.

---

# PHASE 18 - Fine-Grained Consent and Permissions

## Goal

Make shared healthcare access explicit.

Possible permissions:

VIEW_MEDICATIONS
VIEW_ADHERENCE
VIEW_DOCUMENTS
VIEW_TIMELINE
RECEIVE_ALERTS

Future doctor permissions may be different.

Do not represent consent as one permanent boolean.

Track:

- who granted access
- who received access
- what is allowed
- when granted
- status
- expiry where applicable
- revocation

## Definition of Done

Permission checks are centralized, tested, and enforced server-side.

---

# PHASE 19 - Doctor Accounts

## Goal

Allow authorized clinicians to participate in continuity of care.

## DoctorProfile

Possible:

- id
- user_id
- full_name
- specialization optional
- registration information where appropriate
- organization relationship later

Do not invent verification claims. A real deployment would need a clinician verification process.

## DoctorPatientAccess

- doctor_id
- patient_id
- status
- permissions
- granted_at
- expires_at optional

## Doctor View

Authorized doctor may see:

- current medicines
- prescription history
- adherence summary
- selected medical documents
- relevant notes
- treatment timeline

## Definition of Done

Doctor sees only patients and information they are authorized to access.

---

# PHASE 20 - Structured Digital Prescriptions

## Goal

Allow an authorized doctor to create a structured prescription.

## Possible Entities

Prescription
PrescriptionItem

PrescriptionItem:
- medicine name
- strength
- form
- dose
- frequency
- duration
- instructions

## Flow

Doctor
 -> structured prescription
 -> patient receives prescription
 -> patient reviews
 -> medication plan generated/confirmed
 -> adherence tracked

## Definition of Done

The original prescription-to-progress loop can begin digitally.

---

# PHASE 21 - Doctor Follow-Up Summary

## Goal

Turn structured patient history into a concise follow-up view.

## Deterministic Layer First

Backend calculates:

- adherence
- missed doses
- delayed doses
- inventory
- new documents
- time since last visit

Gemini may summarize these verified facts.

Example:

Since your last visit:

- Medication adherence: 92%
- 2 evening doses missed
- 1 medicine nearing refill
- 30 days treatment history available

## Definition of Done

Doctor can view a concise, grounded summary with links back to source records.

---

# PHASE 22 - Hospital / Organization Layer

## Goal

Support healthcare organizations without making the hospital own the patient's entire history.

## Possible Entities

Hospital
HospitalMembership
Visit
HospitalPatientRelationship

## Capabilities

- organization account
- staff/doctor membership
- patient visits
- structured prescriptions
- authorized report uploads
- discharge documents
- role-based access

## Core Vision

Hospital A \
Hospital B  -> Patient-controlled CareMate history
Clinic C   /

## Definition of Done

Organization-scoped access is separate from patient identity and consent is enforced.

---

# PHASE 23 - Notification Foundation

## Goal

Send reminders and useful system notifications.

## Types

- medicine due
- low stock
- prescription received
- caregiver invitation
- document processing completed
- follow-up reminder

Start with in-app notification representation if external delivery is not ready.

## Architecture

Domain event / scheduled job
 -> NotificationService
 -> notification record
 -> delivery channel

## Definition of Done

Notifications are generated reliably without mixing notification logic throughout route handlers.

---

# PHASE 24 - Scheduled Medication Reminders

## Goal

Turn medication schedules into real reminders.

Potential technologies must be selected based on deployment needs:

- FastAPI BackgroundTasks are NOT a durable scheduler by themselves
- APScheduler may work for simpler deployments
- Celery/RQ plus Redis may become appropriate for durable distributed jobs

Do not add Celery merely because it sounds production-grade. Choose after requirements are understood.

## Definition of Done

Due medication reminders are produced reliably in the chosen environment.

---

# PHASE 25 - Caregiver Escalation

## Goal

Notify caregivers only when patient-authorized rules justify it.

Avoid:

One minor delay -> panic notification.

Prefer meaningful conditions such as:

- repeated missed doses
- persistent low stock
- configurable patient preferences

Rules should initially be deterministic.

## Definition of Done

Escalations are consent-aware, configurable, and tested.

---

# PHASE 26 - Context-Aware CareMate Assistant

## Goal

Allow natural-language interaction with authorized CareMate data.

The assistant is NOT generic ChatGPT embedded in the UI.

## Request Flow

Question
 -> authenticated actor
 -> permission check
 -> classify/retrieve required CareMate data
 -> deterministic answer if possible
 -> Gemini only when interpretation/summarization helps
 -> grounded response

Examples:

"When did I last take Metformin?"

Prefer database query.

"Summarize how I have been doing with my medicines this month."

Retrieve verified data and let Gemini summarize.

## Definition of Done

Assistant answers from authorized CareMate context and does not fabricate patient records.

---

# PHASE 27 - RAG Over Medical Documents

## Goal

Allow CareMate to retrieve relevant portions of authorized medical documents.

Only begin after document storage and ordinary AI workflows are stable.

## Conceptual Pipeline

Document
 -> text extraction
 -> chunking
 -> embeddings
 -> vector storage
 -> retrieval
 -> permission filter
 -> Gemini
 -> grounded answer

The exact vector database should be chosen later based on requirements.

Never retrieve another patient's chunks.

## Definition of Done

Questions over medical documents return answers grounded in retrieved authorized source content.

---

# PHASE 28 - Adherence Pattern Intelligence

## Goal

Identify useful behavioral patterns from structured event data.

Start deterministic.

Examples:

- morning adherence 98%
- evening adherence 72%
- repeated weekend misses
- average delay

Gemini can explain a calculated pattern but should not invent the metric.

Potential future research may explore predictive models after sufficient legitimate data exists.

## Definition of Done

Insights can be traced back to explicit calculations.

---

# PHASE 29 - Adaptive Reminder Suggestions

## Goal

Suggest better reminder strategies based on observed behavior.

Example:

Scheduled: 20:00

Actual pattern:
20:47
20:51
20:42
MISSED
20:56

CareMate may suggest that the patient adjust reminder strategy.

CareMate must not independently alter prescribed medical dosage/timing.

## Definition of Done

Suggestions are explainable, optional, and require user action.

---

# PHASE 30 - Frontend Foundation

Frontend can begin earlier, preferably after the core backend around Phase 10 is stable. This phase number represents the full roadmap, not a mandatory waiting point.

## Initial Pages

/register
/login
/dashboard
/medicines
/medicines/:id
/schedule
/history
/documents
/timeline
/profile

Later:

/caregivers
/assistant
/doctor/*
/hospital/*

## Suggested Feature Structure

src/
|-- api/
|-- components/
|-- pages/
|-- hooks/
|-- context/
|-- utils/
`-- features/
    |-- auth/
    |-- medicines/
    |-- schedules/
    |-- adherence/
    |-- inventory/
    |-- documents/
    |-- timeline/
    `-- caregivers/

## Rule

Do not duplicate backend business rules in React.

## Definition of Done

Core patient journey works end to end through the browser.

---

# PHASE 31 - Comprehensive Testing

Testing occurs in EVERY phase. This phase represents hardening.

## Unit Tests

Examples:

- AdherenceService
- InventoryService
- permission checks
- medication event transitions

## API / Integration Tests

Examples:

- register
- login
- medicine CRUD
- schedule
- event status
- document upload

## Security Tests

- Patient A cannot access Patient B medicine.
- Patient A cannot access Patient B document.
- Caregiver without permission cannot access adherence.
- Doctor without active access cannot retrieve patient records.
- invalid JWT -> 401
- expired JWT -> 401

## AI Tests

Mock external Gemini calls where appropriate.

Test:

- timeout
- malformed JSON
- missing fields
- rejected extraction
- unavailable API

## Definition of Done

Critical workflows and authorization boundaries have automated coverage.

---

# PHASE 32 - Audit Logging and Security Hardening

## Goal

Improve accountability and production security.

Potential AuditLog:

- actor
- action
- resource type
- resource id
- timestamp
- outcome

Examples:

Doctor viewed Prescription X.
Caregiver viewed adherence summary.
Patient revoked caregiver access.

Additional work:

- rate limiting
- strict validation
- secure headers
- token strategy review
- file authorization
- safe logging
- CORS configuration
- account/session controls
- dependency security review

## Definition of Done

Sensitive actions are protected and important access is auditable.

---

# PHASE 33 - Docker and Production Deployment

## Goal

Make CareMate reproducibly deployable.

## Components

- FastAPI container
- PostgreSQL
- migration execution
- environment configuration
- frontend deployment
- production file/object storage
- HTTPS
- logging
- backups
- monitoring

Use Alembic migrations.

Never rely on development auto-table creation as a production migration strategy.

## Definition of Done

A clean environment can deploy the documented CareMate release reproducibly.

---

# PHASE 34 - CI/CD

## Goal

Prevent broken code from reaching deployment.

Pipeline may:

1. install dependencies
2. lint/format if adopted
3. run tests
4. verify migrations
5. build container
6. deploy after appropriate approval

Do not introduce complex CI before tests are meaningful.

---

# PHASE 35 - Advanced / Research Features

These are NOT required for initial CareMate.

Possible future work:

- emergency QR profile with pre-authorized information
- multilingual interface
- voice assistant
- offline/low-connectivity synchronization
- dependent/family accounts
- pharmacy integration
- refill ordering
- verified drug database integration
- drug interaction checks using authoritative sources
- appointment integration
- lab integrations
- wearable integration
- adherence-risk research
- adaptive reminder research
- explainable caregiver escalation
- cross-institution patient-controlled medication continuity

Patentability must never be assumed. Any IP claim requires prior-art research and professional advice.

---

# 12. Recommended Practical Milestones

The numbered phases above are intentionally detailed. For project management, group them into these milestones.

## MILESTONE A - FastAPI Core

Phases 0-4

Result:

Repository
 -> FastAPI
 -> PostgreSQL
 -> Authentication
 -> Patient profile

## MILESTONE B - Working Medication Tracker

Phases 5-10

Result:

Medicine
 -> Schedule
 -> Event
 -> Adherence
 -> Inventory
 -> Dashboard

At this point CareMate is already a functioning backend product.

## MILESTONE C - Continuity of Care

Phases 11-14

Result:

Health notes
 -> Medical documents
 -> Prescriptions
 -> Timeline

This is where CareMate clearly becomes more than a reminder application.

## MILESTONE D - Gemini Intelligence

Phases 15-16

Result:

Prescription
 -> Gemini extraction
 -> validated draft
 -> human confirmation
 -> structured treatment

## MILESTONE E - Connected Care

Phases 17-22

Result:

Caregiver
 -> Consent
 -> Doctor
 -> Digital prescription
 -> Follow-up summary
 -> Hospital

This creates the closed-loop care vision.

## MILESTONE F - Intelligent Care

Phases 23-29

Result:

Notifications
 -> reminders
 -> caregiver escalation
 -> CareMate assistant
 -> RAG
 -> adherence insights
 -> adaptive suggestions

## MILESTONE G - Productization

Phases 30-34

Result:

Frontend
 -> tests
 -> security
 -> Docker
 -> deployment
 -> CI/CD

---

# 13. Recommended First End-to-End Vertical Slice

Before chasing advanced features, achieve this exact flow:

Patient registers
    |
Patient logs in
    |
Receives JWT
    |
Creates medicine
    |
Creates medication schedule
    |
CareMate creates/returns today's medication event
    |
Patient marks dose TAKEN
    |
Adherence updates
    |
Inventory decreases
    |
Dashboard reflects the change

If this flow is reliable, the foundation is healthy.

---

# 14. API Design Principles

Prefer RESTful resource-oriented endpoints.

Use consistent prefixing, for example:

/api/v1/auth
/api/v1/profile
/api/v1/medicines
/api/v1/schedules
/api/v1/medication-events
/api/v1/dashboard
/api/v1/documents
/api/v1/prescriptions
/api/v1/timeline

Use proper status codes.

Examples:

200 successful retrieval
201 resource created
204 successful deletion where appropriate
400 malformed business request
401 unauthenticated
403 authenticated but unauthorized
404 resource not found
409 conflict such as duplicate resource where appropriate
422 validation error

Do not return internal stack traces to clients.

---

# 15. Error Handling Strategy

Eventually introduce consistent domain errors.

Examples:

MedicineNotFound
DocumentNotFound
UnauthorizedResourceAccess
InvalidMedicationEventTransition
DuplicateEmail
InvalidPrescriptionDraft

API responses should be predictable.

Do not expose database implementation details.

---

# 16. Date and Time Rules

Medication systems depend heavily on time.

Do not casually use naive timestamps everywhere.

Before medication-event scheduling is finalized:

- decide how patient timezone is stored
- store canonical timestamps appropriately
- convert for display
- test daylight/timezone behavior relevant to supported regions

For an early India-only prototype this may appear simple, but architecture should not permanently assume all users share one timezone.

---

# 17. Database Migration Rules

Once Alembic is introduced:

- schema changes require migrations
- migration files should be reviewed
- never delete production data casually
- do not rewrite old applied migrations without understanding consequences
- seed/demo data must be separate from production data

---

# 18. File Storage Rules

Development may use local storage.

Production should use a suitable object storage solution.

The database stores metadata and storage references, not necessarily the entire file binary.

Validate:

- content type
- extension where useful
- maximum size
- authorization
- safe generated storage names

Never trust the uploaded filename as a filesystem path.

---

# 19. Gemini Integration Rules

All Gemini calls go through an isolated client/service.

Do not scatter SDK calls throughout route files.

Recommended conceptual split:

GeminiClient
 -> low-level API communication

PrescriptionExtractionService
 -> prescription-specific AI workflow

MedicalSummaryService
 -> summarization

CareMateAssistantService
 -> context-aware assistant

Prompts should be versionable and testable.

Structured responses must be validated with Pydantic before entering domain logic.

---

# 20. Deterministic Logic vs AI Logic

Use ordinary code/database logic for:

- authentication
- authorization
- next scheduled dose
- adherence percentages
- inventory quantity
- days remaining when mathematically calculable
- retrieving latest prescription
- timestamps
- permission checks
- event transitions

Use Gemini where language understanding helps:

- interpreting prescription text
- organizing unstructured document content
- summarizing longitudinal history
- explaining already-calculated adherence patterns
- natural-language interaction with retrieved patient context

Rule:

If a SQL query or normal Python function can answer the question reliably, prefer that over asking an LLM.

---

# 21. Demo Data Strategy

Create safe fictional demo accounts/data for development and competition demonstrations.

Never commit real medical records.

Demo story can represent:

- elderly patient
- adult caregiver
- doctor
- prescription
- Metformin or another clearly fictional/demo treatment context
- 30-day adherence history
- a low-stock medicine
- a lab report
- follow-up summary

Label demo data appropriately.

---

# 22. README Expectations

README should eventually explain:

1. What CareMate is.
2. Problem being solved.
3. Architecture.
4. Tech stack.
5. Current implemented features.
6. Local setup.
7. Environment variables.
8. Database migration commands.
9. Test commands.
10. API documentation location.
11. Project roadmap.
12. Safety/privacy limitations.
13. Screenshots/demo when frontend exists.

Do not claim unimplemented roadmap features as completed.

---

# 23. DEVELOPMENT_PROGRESS.md Template

Maintain a file with a structure similar to:

# CareMate Development Progress

Current Phase: 1

## Completed

- [x] Phase 0 - Repository foundation

## Current

- [ ] Phase 1 - FastAPI foundation

### Current Tasks

- [ ] Create FastAPI application
- [ ] Add health endpoint
- [ ] Run Uvicorn
- [ ] Add first test

## Not Started

- [ ] Phase 2 - PostgreSQL / SQLAlchemy / Alembic
- [ ] Phase 3 - Authentication
- [ ] Phase 4 - Patient profile
- [ ] Phase 5 - Medicine management
...

## Decisions

Record important architectural decisions here.

## Known Issues

Record unresolved bugs here.

## Next Session

State exactly what the next coding session should begin with.

The coding agent must update this file after each completed phase.

---

# 24. Definition of Project Success

CareMate should eventually demonstrate this story:

1. A doctor creates or a patient uploads a prescription.
2. CareMate understands and organizes it.
3. The patient confirms the treatment information.
4. Medication schedules are created.
5. CareMate records what happens between appointments.
6. Inventory and adherence are tracked.
7. Medical records remain organized.
8. A caregiver can participate only with patient permission.
9. At follow-up, an authorized doctor can quickly understand what happened.
10. Gemini helps interpret and summarize the authorized information without replacing deterministic healthcare logic or clinician judgment.

The product should communicate:

Doctor knows what they prescribed.
Patient knows what happened afterward.
CareMate connects the two.

---

# 25. First Prompt for Claude Code / Codex

Use this after placing this file in the repository:

Read CAREMATE_MASTER_SPEC.md completely.

Then read DEVELOPMENT_PROGRESS.md if it exists and inspect the current repository.

This specification is the authoritative long-term architecture for CareMate, but you MUST NOT implement the entire specification.

Determine the current unfinished phase and work only on that phase.

Before writing code:

1. Tell me what already exists in the repository.
2. Explain what the current phase will accomplish.
3. Explain the FastAPI/Python concepts I need to understand.
4. List the files you propose to create or modify.
5. Explain any database changes.
6. Explain the API endpoints involved.
7. Point out security implications.
8. Give me the implementation plan.

I am learning FastAPI while building this project, so do not hide important behavior behind unexplained abstractions.

Prefer clean, understandable, production-oriented Python.

Do not implement future phases early.

Do not add Gemini until the Gemini phases.

Do not add caregivers, doctors, hospitals, RAG, or advanced infrastructure until their phases.

After I approve the plan, implement only the current phase, run relevant tests, fix errors, explain the changes, update DEVELOPMENT_PROGRESS.md, and stop.

---

# 26. Prompt for Continuing on a Later Day

Read CAREMATE_MASTER_SPEC.md and DEVELOPMENT_PROGRESS.md.

Inspect the repository and verify that DEVELOPMENT_PROGRESS.md matches the actual code.

Continue from the first unfinished phase.

Do not assume previously planned code exists unless you can see it in the repository.

Before making changes, summarize:

- what is already working
- what phase we are on
- what we are building next
- files that will change
- concepts I should understand

Then follow the phase rules from CAREMATE_MASTER_SPEC.md.

---

# 27. Debugging Prompt

When something breaks, use:

Inspect the current CareMate repository and the error below.

Do not rewrite unrelated parts of the application.

First explain:

1. What the error means in simple terms.
2. The most likely root cause.
3. Which part of our architecture is involved.
4. What you intend to change.

Then make the smallest correct fix.

Run the relevant command/test again and verify the result.

After fixing it, explain why the fix works.

Do not advance to another CareMate phase.

---

# 28. Code Review Prompt

Periodically use:

Review the currently implemented CareMate code against CAREMATE_MASTER_SPEC.md.

Do not implement future features.

Look specifically for:

- broken authorization or ownership checks
- unnecessary complexity
- duplicated business logic
- routes containing too much business logic
- unsafe password/JWT handling
- secrets committed to code
- SQLAlchemy session mistakes
- missing validation
- poor error handling
- inconsistent schemas
- missing tests
- medical files exposed without authorization
- AI code being used where deterministic code should be used

Explain findings by severity and teach me why each issue matters.

Do not refactor anything until I approve the review plan.

---

# 29. Final Rule

The objective is NOT to maximize the amount of generated code.

The objective is to build a CareMate codebase that:

- works
- is secure
- is understandable
- can be tested
- can evolve
- demonstrates a real continuity-of-care concept
- can be confidently explained by its developer

Build one reliable layer at a time.
