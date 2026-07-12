# Contract Change Record: CCR-001

Contract: `POST /api/v1/people/bulk-actions`

Current shape: No bulk People mutation endpoint exists. Clients call single-person update/archive/activity endpoints.

New shape:

```http
POST /api/v1/people/bulk-actions
Authorization: Bearer <Supabase JWT>
Content-Type: application/json
```

Request (unknown fields rejected):

```json
{
  "workspace_id": "uuid",
  "person_ids": ["uuid"],
  "action": "set_favorite | add_tags | remove_tags | set_priority | set_stage | archive | set_next_action",
  "payload": {}
}
```

Validation shared by all actions:

- `person_ids`: 1–100 entries; duplicate IDs rejected with `VALIDATION_ERROR` message `Select each person only once.`
- Every ID must identify an active, non-deleted person in `workspace_id`. Otherwise 404 `NOT_FOUND`, message `One or more people not found.` and zero mutations.
- `action` must match one allowed value.
- `payload` is action-specific and rejects unknown/missing fields.

Payloads:

- `set_favorite`: `{ "is_favorite": boolean }`.
- `add_tags`: `{ "tags": string[1..20] }`; each trimmed tag 1–50 chars; final person tag set max 20; matching is case-sensitive in `v0.0.1`; duplicates removed preserving first occurrence.
- `remove_tags`: same tag validation; absent tags are no-ops.
- `set_priority`: `{ "priority": "A" | "B" | "C" }`.
- `set_stage`: `{ "stage": "saved_for_later" | "invite_sent" | "invite_pending" | "accepted" | "waiting_for_reply" | "replied" | "archived" }`. Non-archived target stages set `status="active"` and preserve next-action fields. Target `archived` sets `status="archived"` and clears next-action fields. Each person whose effective state changes receives one `activities` row with `action_type="bulk_stage_change"`, `source="web_app"`, previous/new stage, actor, and notes `Bulk stage change`; `last_action_type` and `last_action_date` are set to that action/today.
- `archive`: `{}`; stage/status become `archived`, next action fields become null. Each person whose effective state changes receives one activity with `action_type="bulk_archive"`, `source="web_app"`, previous/new stage and notes `Bulk archive`; `last_action_type` and `last_action_date` are set to that action/today.
- `set_next_action`: `{ "next_action_type": string|null, "next_action_date": "YYYY-MM-DD"|null }`; `next_action_type` trimmed max 100; both may be null to clear.

Success:

```json
{
  "updated_count": 2,
  "items": ["PersonResponse", "PersonResponse"]
}
```

- 200 even when valid values already match; `updated_count` equals selected people count.
- Items return in request ID order.

Errors use the existing repository envelope:

- 401 `UNAUTHORIZED` for missing/invalid auth.
- 403 `FORBIDDEN` for no workspace membership (existing `require_workspace_access`).
- 404 `NOT_FOUND` for any missing/cross-workspace/deleted person, generic message above.
- 422 `VALIDATION_ERROR` for domain validation; framework validation remains the existing FastAPI 422 shape until a separate error-normalization CCR.
- 500 `INTERNAL_ERROR`, transaction rolled back.

Reason: Users need one safe mutation for explicit People selections instead of many independent requests that can partially fail and leave inconsistent state.

Breaking? no — additive endpoint only.

Compatibility plan: existing single-person endpoints remain unchanged. Frontend falls back only by surfacing an error; it must not emulate partial bulk mutations client-side.

Migration plan: no schema migration. Existing `people.tags`, People state fields and `activities` are reused. Rollback removes the new route/schema/service method/frontend calls.

Downstream impact:

- Tickets affected: `MAS-1.1` backend contract; `MAS-1.2` frontend selection/actions; `MAS-1.3` integration/release evidence.
- Code affected: `backend/app/schemas/people.py`, `backend/app/services/bulk_people_service.py`, `backend/app/api/routes/people.py`, `backend/app/tests/integration/conftest.py`, `backend/app/tests/integration/test_people_api.py`, `frontend/src/api/httpClient.ts`, `frontend/src/features/bulk-actions/*`, `frontend/src/pages/PeopleListPage.tsx`, related frontend tests, `docs/API_SPEC.md`.
- Tickets already merged that must be re-opened: none.

Updated artifacts: [x] architecture plan [ ] affected tickets [x] repo_context.md
