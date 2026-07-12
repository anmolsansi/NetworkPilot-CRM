# TICKET MAS-1.1: Atomic Bulk People API

## Goal

Add one workspace-scoped, atomic API endpoint that applies an approved bulk action to 1–100 selected people.

## Why This Exists

Users currently perform repeated single-person requests, which is slow and can partially succeed. `v0.0.1` needs one server-authoritative operation with validation and transaction rollback.

## User-Facing Behavior

The future People bulk toolbar receives all updated people after one request. If any selected person is invalid or inaccessible, no selected person changes and the user sees a safe error.

## Scope

- Add the frozen `POST /api/v1/people/bulk-actions` contract from CCR-001.
- Validate the discriminated action/payload at the Pydantic boundary and reject unknown fields.
- Load all selected people in one workspace-scoped query and preserve request order.
- Abort before mutation if any ID is missing, deleted, duplicated, or cross-workspace.
- Apply `set_favorite`, `add_tags`, `remove_tags`, `set_priority`, `set_stage`, `archive`, and `set_next_action` atomically.
- Add an Activity row per changed person for `set_stage` and `archive`.
- Add HTTP integration tests and update `docs/API_SPEC.md`.

## Out of Scope

- Frontend selection, toolbar, modal, or API call.
- Selecting all people across pages or filters.
- Persistent bulk-operation history, undo, job queues, custom tag definitions, or RBAC beyond current workspace membership.
- Changes to single-person endpoints or transition-service behavior.

## Files to Inspect First

- `backend/app/schemas/people.py` — current Person contracts and Pydantic style.
- `backend/app/services/people_service.py` — workspace-scoped queries, updates, archives and domain errors.
- `backend/app/api/routes/people.py` — route/auth/logging order; static bulk route must precede `/{person_id}`.
- `backend/app/tests/integration/test_people_api.py` — HTTP fixture and assertion conventions.
- `backend/app/models/activity.py` — exact activity columns.

## Files to Create or Edit

- Edit `backend/app/schemas/people.py`.
- Create `backend/app/services/bulk_people_service.py`.
- Edit `backend/app/api/routes/people.py`.
- Edit `backend/app/tests/integration/test_people_api.py`.
- Edit `backend/app/tests/integration/conftest.py`.
- Edit `docs/API_SPEC.md`.

## Data Model

No schema migration. Reuse `people` fields and `activities` columns exactly as they exist. `set_stage` and `archive` add Activity rows with current UUID defaults and `created_at` default.

## API Contract

Use CCR-001 exactly. Summary:

`POST /api/v1/people/bulk-actions`; Supabase bearer JWT required; route explicitly calls `require_workspace_access(data.workspace_id, user, db)`.

Top-level discriminated union variants share:

- `workspace_id: UUID`, required.
- `person_ids: list[UUID]`, 1–100, unique.
- `action: Literal[...]`, discriminator.
- `payload`, required action-specific Pydantic model.
- Every new request/payload model uses `ConfigDict(extra="forbid")`.

Payloads and exact validation are copied from `docs/contract_changes/CCR-001-bulk-people-actions.md` and are frozen.

200:

```json
{"updated_count": 2, "items": ["PersonResponse", "PersonResponse"]}
```

401/403 use existing auth/workspace errors. 404 is `NOT_FOUND` with message `One or more people not found.`. Domain validation is 422 existing `VALIDATION_ERROR`. Unexpected failure is 500 and request transaction rolls back.

## UI States

None (API ticket).

## Validation Rules

1. Empty/more than 100 IDs → boundary 422.
2. Duplicate IDs → domain-style 422 with message `Select each person only once.`
3. Missing/deleted/cross-workspace ID → 404 message `One or more people not found.`; no mutation.
4. Tags: 1–20 input strings, trim each, 1–50 chars, de-duplicate preserving first; final tags ≤20 or 422 `A person can have at most 20 tags.`
5. Priority: exactly A/B/C.
6. Stage: exactly the seven CCR values; apply the status/next-action/last-action invariants frozen in CCR-001.
7. Next action type: nullable, trimmed, max 100; date nullable ISO date.
8. Unknown top-level/payload fields → boundary 422.

## Error Handling

- Validate all selected records and computed final tag lists before changing ORM objects.
- Any exception propagates to `get_db`, which rolls back the request transaction.
- Do not include missing IDs, profile values, tags, notes, or request bodies in logs/errors.
- Return generic not-found for a cross-workspace ID to avoid enumeration.

## Auth & Permissions

Authenticated active workspace owner/member may call it under the current permission model. Use `get_current_user`, then `require_workspace_access`. Every Person query includes `Person.workspace_id == data.workspace_id` and `Person.deleted_at.is_(None)`.

## Dependencies

- CCR-001 frozen.
- Existing People/Activity models and workspace authorization merged on `main`.
- No unmerged ticket dependency.

## Integration Contract

Exposes the exact endpoint in CCR-001 to MAS-1.2. Existing single-person routes and `PersonResponse` remain unchanged.

## Implementation Steps

1. Add strict payload/request union and response schemas.
2. Add `BulkPeopleService.apply(workspace_id, actor_user_id, data)` with bounded load/refresh queries, full prevalidation, ordered mutation and Activity creation; keep `PeopleService` focused on single/list operations.
3. Add the static bulk route before `/{person_id}`, explicit current-user/workspace access, safe structured logs and response validation.
4. Make the SQLite integration fixture bind/result-process PostgreSQL ARRAY columns as JSON so tag behavior is tested against a real database write.
5. Add integration coverage for every action class, atomic failure, workspace isolation, validation and auth.
6. Document endpoint in `docs/API_SPEC.md`; run focused and full backend tests.

## Test Cases

1. Set favourite for two workspace people → 200, ordered items, both persisted.
2. Add/remove tags → trims/de-duplicates, preserves unrelated tags, enforces final max 20.
3. Set priority A/B/C → persists exact value.
4. Set stage → Activity per person with correct previous/new stage, actor and source.
5. Archive → state fields cleared and Activity created.
6. Set/clear next action → exact type/date/null persistence.
7. Empty, 101, duplicate IDs, wrong action payload, unknown fields, long tag/type → 422.
8. One missing/deleted/cross-workspace ID mixed with valid ID → 404 and valid person unchanged.
9. Missing auth → 401.
10. Valid auth without workspace membership → 403.
11. Full backend suite remains green.

## Manual QA

1. Create two test people in one workspace.
2. Call each action through local Swagger/curl and verify 200/order/state.
3. Mix one foreign/missing ID with a local ID and verify 404 plus unchanged local row.
4. Refresh People/detail and verify state/activity display remains valid.

## Acceptance Criteria

- [ ] CCR-001 request/response/action contracts are exact.
- [ ] All seven actions are atomic and workspace-scoped.
- [ ] Activity rows are created only for stage/archive actions as specified.
- [ ] Test cases 1–11 pass.
- [ ] API documentation is updated.
- [ ] Only the six allowed files are edited.

## Definition of Done

Complete `product_quality_bar.md`, including focused/full tests and a Done Report. No migration is expected.

## Do Not Change

- Database migrations/models, transition service, activity service, single-person endpoint contracts, frontend/extension code, auth/JWT/workspace authorization behavior, error envelope. `conftest.py` changes are limited to PostgreSQL ARRAY-as-JSON test emulation.

## Build Order

Phase 1: MAS-1.1.  
Phase 2 after MAS-1.1 merge: MAS-1.2 frontend selection/actions.  
Phase 3 after integration: MAS-1.3 release evidence/tag preparation.  
Blocked: MAS-1.2 integration call → MAS-1.1 endpoint merge.
