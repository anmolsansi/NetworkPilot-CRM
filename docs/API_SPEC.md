# API Spec

Base URL: `/api/v1`

## Authentication

All endpoints except `/health` require:
```
Authorization: Bearer <supabase_access_token>
```

## Common Error Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human readable message",
    "details": {}
  }
}
```

## Endpoints

### Health

```
GET /health
```

Response:
```json
{ "status": "ok", "service": "networkpilot-api" }
```

### Users

```
GET /me
```

Returns current user and workspace memberships.

### Workspaces

```
GET    /workspaces
POST   /workspaces
PATCH  /workspaces/{workspace_id}
```

### People

*Requires `workspace_id` as a query parameter for all endpoints.*
```
GET    /people?workspace_id=&stage=&stage_id=&tag_id=&priority=&status=&search=&deleted_only=&page=&limit=
POST   /people?workspace_id=
GET    /people/{person_id}?workspace_id=
PATCH  /people/{person_id}?workspace_id=
DELETE /people/{person_id}?workspace_id=
POST   /people/{person_id}/restore?workspace_id=
POST   /people/{person_id}/unarchive?workspace_id=
```

#### Atomic bulk People actions (`v0.0.1`)

Unlike the single-person endpoints, `workspace_id` is required in the JSON body:

```http
POST /people/bulk-actions
```

```json
{
  "workspace_id": "uuid",
  "person_ids": ["uuid"],
  "action": "set_favorite | add_tags | remove_tags | set_priority | set_stage | archive | set_next_action",
  "payload": {}
}
```

The request accepts 1–100 unique people and is atomic: if any selected person is missing,
deleted, or outside the workspace, the endpoint returns 404 and changes none of them.
Action payloads:

- `set_favorite`: `{ "is_favorite": boolean }`
- `add_tags` / `remove_tags`: exactly one of `{ "tags": [string] }` or `{ "tag_ids": [uuid] }`
- `set_priority`: `{ "priority": "A" | "B" | "C" }`
- `set_stage`: exactly one of the legacy `{ "stage": "..." }` contract or `{ "stage_id": uuid|null }`
- `archive`: `{}`
- `set_next_action`: `{ "next_action_type": string|null, "next_action_date": "YYYY-MM-DD"|null }`

Success returns the selected people in request order:

```json
{
  "updated_count": 2,
  "items": ["PersonResponse", "PersonResponse"]
}
```

CSV import accepts NetworkPilot headers and Octopus Connect exports. Octopus columns map as
`Link → linkedin_url`, `First name`/`Last name → first_name`/`last_name`,
`Position → role`, with email, phone, Premium, location, company website, processed time,
and invite-accepted time preserved on the person record.

CSV commit is asynchronous and limited to 10 MB. `POST /imports/people/commit` accepts a
multipart CSV, queues a durable job, and returns its status immediately. The worker processes
40 rows per checkpoint. Jobs remain visible after the browser closes, recover after stale worker
leases, and support at most three attempts.

```
GET  /imports?workspace_id=
GET  /imports/{job_id}?workspace_id=
POST /imports/{job_id}/retry?workspace_id=
GET  /imports/{job_id}/errors.csv?workspace_id=
```

### Saved views and duplicates

```
GET|POST       /saved-views?workspace_id=
PATCH|DELETE   /saved-views/{view_id}?workspace_id=
GET            /people/duplicates?workspace_id=
POST           /people/duplicates/merge?workspace_id=
```

Saved filters and sort keys are server-allowlisted. View names are unique per user/workspace.
Duplicate groups use normalized LinkedIn URL, email, or name plus company. Merge fields are
strictly allowlisted; tags and workspace-scoped activities are moved atomically.

### Tags, pipeline stages, and custom fields

```
GET|POST       /tags
PATCH|DELETE   /tags/{tag_id}?workspace_id=
GET|POST       /pipeline-stages?workspace_id=
PATCH|DELETE   /pipeline-stages/{stage_id}?workspace_id=
POST           /pipeline-stages/reorder?workspace_id=
GET|POST       /custom-fields?workspace_id=
PUT|DELETE     /custom-fields/{field_id}?workspace_id=
```

Tags have validated names and hex colours. Pipeline stage names/orders are workspace-unique and
may define `allowed_next_stage_ids`. Custom person values use stable custom-field UUIDs as JSON
keys and are validated by type; supported types are text, number, date, boolean, and select.

### Activities

*Requires `workspace_id` as a query parameter for all endpoints.*
```
GET  /people/{person_id}/activities?workspace_id=&limit=&offset=
POST /people/{person_id}/activities?workspace_id=
```

### Quick Actions

*Requires `workspace_id` as a query parameter for all endpoints.*
```
POST /people/{person_id}/snooze?workspace_id=
POST /people/{person_id}/archive?workspace_id=
```

### Dashboard

*Requires `workspace_id` as a query parameter for all endpoints.*
```
GET /dashboard/summary?workspace_id=
GET /dashboard/due?workspace_id=&date=&include_overdue=&priority=
GET /dashboard/tags?workspace_id=
```

### Templates

*Requires `workspace_id` as a query parameter for all endpoints.*
```
GET    /templates?workspace_id=&category=
POST   /templates?workspace_id=
PATCH  /templates/{template_id}?workspace_id=
DELETE /templates/{template_id}?workspace_id=
```

### Calendar

*Requires `workspace_id` as a query parameter for all endpoints.*
```
GET /calendar/daily-reminder-link?workspace_id=
```

### Extension

```
GET  /extension/lookup?workspace_id=&linkedin_url=
POST /extension/quick-create  (workspace_id required in JSON body)
POST /extension/quick-action  (workspace_id required in JSON body)
POST /extension/favorite      (workspace_id required in JSON body)
```

### Notifications and reminder preferences

```
GET  /notifications?workspace_id=&unread_only=
POST /notifications/{notification_id}/read?workspace_id=
POST /notifications/read-all?workspace_id=
```

Workspace settings include timezone, digest time, quiet-hours start/end, and channel toggles for
daily digests, overdue alerts, and email reminders.
