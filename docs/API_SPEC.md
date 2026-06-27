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

```
GET    /people?workspace_id=&stage=&priority=&status=&search=&page=&limit=
POST   /people
GET    /people/{person_id}
PATCH  /people/{person_id}
DELETE /people/{person_id}
```

### Activities

```
GET  /people/{person_id}/activities?limit=&offset=
POST /people/{person_id}/activities
```

### Quick Actions

```
POST /people/{person_id}/snooze
POST /people/{person_id}/archive
```

### Dashboard

```
GET /dashboard/summary?workspace_id=
GET /dashboard/due?workspace_id=&date=&include_overdue=&priority=
```

### Templates

```
GET    /templates?workspace_id=&category=
POST   /templates
PATCH  /templates/{template_id}
DELETE /templates/{template_id}
```

### Calendar

```
GET /calendar/daily-reminder-link?workspace_id=
```

### Extension

```
GET  /extension/lookup?workspace_id=&linkedin_url=
POST /extension/quick-create
POST /extension/quick-action
```
