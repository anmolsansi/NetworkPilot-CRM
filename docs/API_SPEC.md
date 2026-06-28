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
