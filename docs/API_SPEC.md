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
GET    /people?workspace_id=&stage=&priority=&status=&search=&page=&limit=
POST   /people?workspace_id=
GET    /people/{person_id}?workspace_id=
PATCH  /people/{person_id}?workspace_id=
DELETE /people/{person_id}?workspace_id=
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
- `add_tags` / `remove_tags`: `{ "tags": [string] }` (1–20 tags, each 1–50 characters)
- `set_priority`: `{ "priority": "A" | "B" | "C" }`
- `set_stage`: `{ "stage": "saved_for_later" | "invite_sent" | "invite_pending" | "accepted" | "waiting_for_reply" | "replied" | "archived" }`
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
```
