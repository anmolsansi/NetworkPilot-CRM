# Contract Change Record: CCR-002

Contract: `Saved People Views`

Current shape: Users cannot save filter and sort combinations.

New shape:

## Database Schema

New table: `saved_people_views`
- `id` (UUID, primary key)
- `workspace_id` (UUID, foreign key to workspaces, index, not null)
- `user_id` (UUID, foreign key to app_users, index, not null)
- `name` (String 100, not null)
- `filters` (JSONB, not null) - Stores the UI filter draft.
- `sort_by` (String 50, not null)
- `sort_order` (String 4, not null)
- `created_at` (Timestamp, not null)
- `updated_at` (Timestamp, not null)

## APIs

Prefix: `/api/v1/saved-views`

### GET `/api/v1/saved-views`
Query: `?workspace_id=<uuid>`
Returns: List of views owned by the `workspace_id` AND `user_id` (the caller).
```json
[
  {
    "id": "uuid",
    "workspace_id": "uuid",
    "user_id": "uuid",
    "name": "Hot Leads",
    "filters": { "stage": "invite_accepted", "priority": "A" },
    "sort_by": "processed_at",
    "sort_order": "desc",
    "created_at": "timestamp",
    "updated_at": "timestamp"
  }
]
```

### POST `/api/v1/saved-views`
Query: `?workspace_id=<uuid>`
Request:
```json
{
  "name": "Hot Leads",
  "filters": { "stage": "invite_accepted", "priority": "A" },
  "sort_by": "processed_at",
  "sort_order": "desc"
}
```
Validation: `name` length 1-100.
Returns: The created view object. Status 201.

### PATCH `/api/v1/saved-views/{id}`
Query: `?workspace_id=<uuid>`
Request (all optional):
```json
{
  "name": "Hotter Leads",
  "filters": {},
  "sort_by": "created_at",
  "sort_order": "asc"
}
```
Validation: View must exist, belong to `workspace_id` AND `user_id`. Otherwise 404 NOT_FOUND.
Returns: Updated view object.

### DELETE `/api/v1/saved-views/{id}`
Query: `?workspace_id=<uuid>`
Validation: View must exist, belong to `workspace_id` AND `user_id`. Otherwise 404 NOT_FOUND.
Returns: 204 No Content.

Errors use the existing repository envelope:
- 401 `UNAUTHORIZED`
- 403 `FORBIDDEN` (missing workspace access)
- 404 `NOT_FOUND`
- 422 `VALIDATION_ERROR`

Reason: Users need to quickly re-apply common filters without manual entry.

Breaking? No, additive.

Compatibility plan: N/A.

Migration plan: Additive Alembic migration.

Downstream impact:
- Tickets: MAS-2.1 (Backend), MAS-2.2 (Frontend).
- UI affected: `PeopleListPage.tsx`

Updated artifacts: [x] architecture plan [ ] affected tickets [x] repo_context.md
