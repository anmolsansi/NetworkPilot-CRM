# Implementation Plan: MAS-1.1 Atomic Bulk People API

## Summary

Add a strict discriminated request union and one atomic workspace-scoped People bulk mutation endpoint so up to 100 explicit selections can be changed without client-side partial failure.

## File-Level Changes

- `backend/app/schemas/people.py`
  - action: edit
  - exact change: add strict payload models, strict discriminated request variants/type alias, uniqueness/tag validators and `BulkPeopleActionResponse`.
- `backend/app/services/bulk_people_service.py`
  - action: create
  - exact change: add ordered workspace load, prevalidation/tag computation, action mutation helpers and direct Activity creation for stage/archive.
- `backend/app/api/routes/people.py`
  - action: edit
  - exact change: import bulk schemas/current-user model/dependency; add static `POST /bulk-actions` before `/{person_id}`; explicitly verify workspace access and log safe counts/action.
- `backend/app/tests/integration/test_people_api.py`
  - action: edit
  - exact change: add HTTP integration cases for seven actions, strict validation, atomic failure, workspace isolation and unauthenticated behavior.
- `backend/app/tests/integration/conftest.py`
  - action: edit
  - exact change: map PostgreSQL ARRAY columns to SQLAlchemy JSON in the SQLite test database before schema creation so list values receive correct bind/result processing.
- `docs/API_SPEC.md`
  - action: edit
  - exact change: document the frozen bulk endpoint contract, payload matrix, atomicity and errors.

## API Changes

Add `POST /api/v1/people/bulk-actions` exactly as frozen in CCR-001. Request is a strict discriminated union on `action`; response is `{updated_count:int,items:PersonResponse[]}`; maximum 100 unique IDs; all-or-nothing mutation.

## Database Changes

None. Reuse People state/tag fields and Activities. Rollback removes route/schema/service code; no data migration.

## Frontend Changes

None.

## Backend Changes

- Pydantic boundary rejects invalid action/payload/unknown fields.
- Service loads all people in one scoped query, verifies exact selection, precomputes tag results, mutates in request order, and flushes once.
- Stage/archive append Activity rows with actor/source/previous/new data.
- Route authenticates current user and verifies workspace access before service invocation.

## Edge Cases

1. Duplicate IDs → 422 `Select each person only once.`
2. Missing/deleted/cross-workspace ID mixed with valid → 404, zero changes.
3. Add tags would push any person above 20 → 422, zero changes.
4. Removing absent tag → successful no-op for that tag.
5. Existing target favourite/priority/stage → successful idempotent state, response count still selection count; activity only when the effective stage/archive state actually changes.
6. Clear next action with both null → both fields null.
7. Unexpected exception before commit → `get_db` rollback.

## Test Cases

1. API happy paths for all seven actions and response order.
2. Persistence and Activity assertions.
3. Boundary validation: empty/101/duplicates/wrong payload/unknown fields/lengths.
4. Atomic missing/deleted/cross-workspace failures.
5. Missing auth and missing membership.
6. Full backend regression suite.

## Execution Split

Safe for builder model: schema definitions, service implementation against frozen contract, route wiring, tests and docs.  
Needs premium model: final review of atomic workspace isolation and enumeration behavior after implementation.

## Open Items

Needs Architect Decision: none.
