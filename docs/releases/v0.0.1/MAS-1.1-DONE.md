# DONE REPORT

Ticket: MAS-1.1 — Atomic Bulk People API

Files changed (builder scope):

- `backend/app/schemas/people.py`
- `backend/app/services/bulk_people_service.py`
- `backend/app/api/routes/people.py`
- `backend/app/tests/integration/test_people_api.py`
- `backend/app/tests/integration/conftest.py`
- `docs/API_SPEC.md`

Tests added:

- `backend/app/tests/integration/test_people_api.py`: bulk favourite/tags/priority/next action, stage/archive activities, strict validation, missing/deleted/cross-workspace atomicity, auth and membership.
- Focused: PASS — 8 tests.
- Full backend: PASS — 78 tests.
- Ruff allowed files: PASS.
- Contract test coverage: PASS — all ticket cases represented.

Manual QA:

- API request/refresh flows, ordered responses, stage/activity persistence, missing/foreign/deleted rollback behavior and auth denial were exercised through the ASGI integration client against a real SQLite transaction database: PASS.
- Browser UI QA: not applicable to API-only MAS-1.1; required in MAS-1.2/MAS-1.3.

Migration: none.  
Data at risk: none.  
Rollback plan: remove the additive route/schema/service/client documentation changes; existing single-person APIs remain unchanged.

Acceptance criteria:

- [x] CCR-001 request/response/action contracts are exact.
- [x] All seven actions are atomic and workspace-scoped.
- [x] Activity rows are created only for effective stage/archive changes.
- [x] Required test cases pass.
- [x] API documentation is updated.
- [x] Builder changes are limited to the six architect-approved files.
- [x] Security review passed: no secret/PII logging, input server validation, explicit auth and workspace-scoped SQL.
- [x] No migration or external dependency introduced.

Needs Architect Decision: none for MAS-1.1. Product decisions for later roadmap releases remain listed in the PRD/architecture and do not block `v0.0.1`.
