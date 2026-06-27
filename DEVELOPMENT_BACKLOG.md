T# Development Backlog

Project: **NetworkPilot CRM**

This backlog converts the V1 product plan into small implementation tickets. Each ticket is scoped so a coding model or developer can complete it in one focused session.

V1 rules:
- Build tracking only.
- Do not automate LinkedIn connection requests or messages.
- Do not scrape LinkedIn inbox, search results, or bulk pages.
- Keep the Chrome extension manual-click only.
- Use the backend as the source of truth for stage transitions and next-action logic.
- Use Supabase Auth, Supabase Postgres, FastAPI, React, and a React Chrome extension.

---

## Phase 1: Project Setup

### Ticket 1: Create Monorepo Structure

Goal:
Create the base repository structure for the web app, backend, extension, and docs.

Context:
The project has three surfaces: React web app, FastAPI backend, and Chrome extension.

Files likely affected:

```text
/package.json
/README.md
/.gitignore
/frontend
/backend
/extension
/docs
```

Implementation steps:
1. Create root folders: `frontend`, `backend`, `extension`, and `docs`.
2. Add root `.gitignore`.
3. Add root `README.md` with local setup order.
4. Add placeholder README files inside each app folder.

Acceptance criteria:
- Repo has separate folders for frontend, backend, extension, and docs.
- `.gitignore` excludes `.env`, `node_modules`, Python cache, build output, logs, and virtual environments.
- Root README explains what each folder is for.

Testing steps:
- Run `ls` and confirm folder structure.
- Confirm no `.env` or secrets are committed.

Do not touch:
- Do not create real app logic yet.
- Do not add database migrations yet.

Depends on:
- None

---

### Ticket 2: Add Planning Docs to `/docs`

Goal:
Store the planning documents inside the repo.

Context:
Coding models need stable reference docs while implementing.

Files likely affected:

```text
/docs/PRODUCT_OVERVIEW.md
/docs/ARCHITECTURE.md
/docs/DATABASE_SCHEMA.md
/docs/API_SPEC.md
/docs/FRONTEND_PLAN.md
/docs/BACKEND_PLAN.md
/docs/DECISIONS.md
/docs/TASKS.md
/README.md
```

Implementation steps:
1. Copy all planning documents into `/docs`.
2. Add links to each doc from root README.
3. Add a short implementation order section in README.

Acceptance criteria:
- All docs exist in `/docs`.
- README links work.
- Docs are not duplicated across app folders.

Testing steps:
- Open README and verify links.
- Confirm filenames match exactly.

Do not touch:
- Do not rewrite product decisions.
- Do not change architecture choices.

Depends on:
- Ticket 1

---

### Ticket 3: Add Root Developer Tooling

Goal:
Add root scripts for installing, linting, formatting, and running the project.

Context:
Multiple coding models may work on the repo, so commands should be predictable.

Files likely affected:

```text
/package.json
/.prettierrc
/.editorconfig
/README.md
```

Implementation steps:
1. Add root `package.json` with workspace scripts.
2. Add formatting config.
3. Add commands for frontend, extension, and backend.
4. Document local commands in README.

Acceptance criteria:
- `npm run dev:frontend` is defined.
- `npm run dev:extension` is defined.
- Backend dev command is documented.
- Formatting rules are consistent.

Testing steps:
- Run `npm install`.
- Run `npm run` and confirm scripts appear.

Do not touch:
- Do not install unnecessary monorepo frameworks.
- Do not introduce Turborepo unless explicitly needed later.

Depends on:
- Ticket 1

---

## Phase 2: Database Setup

### Ticket 4: Create Supabase Project Setup Notes

Goal:
Document how to create and configure the Supabase project.

Context:
Supabase handles Postgres and Auth for V1.

Files likely affected:

```text
/docs/SUPABASE_SETUP.md
/backend/.env.example
/frontend/.env.example
/extension/.env.example
```

Implementation steps:
1. Create `SUPABASE_SETUP.md`.
2. Document required Supabase values.
3. Add `.env.example` files for backend, frontend, and extension.
4. Mention local and hosted environment differences.

Acceptance criteria:
- Required environment variables are clearly listed.
- No real Supabase keys are committed.
- Setup doc explains Auth and Database configuration.

Testing steps:
- Review setup doc from a fresh developer perspective.
- Confirm `.env.example` files contain placeholders only.

Do not touch:
- Do not add production secrets.
- Do not enable paid Supabase features.

Depends on:
- Ticket 1

---

### Ticket 5: Initialize Backend Database Layer

Goal:
Add SQLAlchemy database engine, session dependency, and base model setup.

Context:
Backend services need one consistent way to access Supabase Postgres.

Files likely affected:

```text
/backend/app/db/session.py
/backend/app/db/base.py
/backend/app/core/config.py
/backend/app/main.py
```

Implementation steps:
1. Add database URL config.
2. Create SQLAlchemy engine.
3. Create session dependency.
4. Add base model import location.

Acceptance criteria:
- Backend can connect to Postgres using `DATABASE_URL`.
- Session dependency can be imported by routes.
- Connection failure gives a clear error.

Testing steps:
- Run a simple database connection test.
- Start FastAPI without hitting routes.

Do not touch:
- Do not create tables manually.
- Do not bypass SQLAlchemy session dependency.

Depends on:
- Ticket 4

---

### Ticket 6: Add Alembic Migration Setup

Goal:
Configure Alembic for database migrations.

Context:
Schema changes should be version-controlled and repeatable.

Files likely affected:

```text
/backend/alembic.ini
/backend/app/db/migrations/env.py
/backend/app/db/migrations/script.py.mako
/backend/app/db/base.py
```

Implementation steps:
1. Initialize Alembic inside backend.
2. Configure Alembic to read backend `DATABASE_URL`.
3. Connect Alembic metadata to SQLAlchemy models.
4. Add migration command instructions.

Acceptance criteria:
- `alembic current` runs.
- `alembic revision --autogenerate` works.
- Migration folder is committed.

Testing steps:
- Run `alembic current`.
- Run a no-op migration generation locally.

Do not touch:
- Do not create the initial schema yet.
- Do not hardcode database credentials.

Depends on:
- Ticket 5

---

### Ticket 7: Implement SQLAlchemy Models

Goal:
Implement all V1 database models.

Context:
The schema needs users, workspaces, workspace members, people, activities, templates, and user settings.

Files likely affected:

```text
/backend/app/models/user.py
/backend/app/models/workspace.py
/backend/app/models/person.py
/backend/app/models/activity.py
/backend/app/models/template.py
/backend/app/models/settings.py
/backend/app/models/__init__.py
/backend/app/db/base.py
```

Implementation steps:
1. Add `AppUser`, `Workspace`, and `WorkspaceMember`.
2. Add `Person`.
3. Add `Activity`.
4. Add `MessageTemplate`.
5. Add `UserSettings`.
6. Define relationships and timestamp fields.

Acceptance criteria:
- Models match `DATABASE_SCHEMA.md`.
- Soft-deletable tables include `deleted_at`.
- Workspace-scoped tables include `workspace_id`.
- Relationships are defined without circular import issues.

Testing steps:
- Import all models in Python shell.
- Run Alembic autogenerate and inspect detected tables.

Do not touch:
- Do not add V2 `integration_connections` logic.
- Do not use MongoDB.
- Do not add hard deletes for people/templates.

Depends on:
- Ticket 6

---

### Ticket 8: Create Initial Database Migration

Goal:
Generate and verify the first migration for all V1 tables.

Context:
This migration becomes the base schema for the project.

Files likely affected:

```text
/backend/app/db/migrations/versions/*.py
```

Implementation steps:
1. Generate migration from SQLAlchemy models.
2. Review generated SQL manually.
3. Add missing indexes or constraints.
4. Run migration against dev database.

Acceptance criteria:
- All V1 tables are created.
- Unique constraints are present for active workspace members, users, templates, and normalized profile URLs.
- Indexes exist for stage, status, priority, due dates, and activity timeline queries.
- Migration can upgrade successfully.

Testing steps:
- Run `alembic upgrade head`.
- Inspect Supabase tables.
- Run `alembic downgrade -1` in local dev database if safe.

Do not touch:
- Do not edit production database manually.
- Do not skip index creation.

Depends on:
- Ticket 7

---

## Phase 3: Backend Foundation

### Ticket 9: Initialize FastAPI App

Goal:
Create the base FastAPI app with health endpoint.

Context:
Backend starts with a simple API foundation before business logic.

Files likely affected:

```text
/backend/pyproject.toml
/backend/app/main.py
/backend/app/api/routes/health.py
/backend/app/api/router.py
```

Implementation steps:
1. Add FastAPI dependencies.
2. Create app factory or main app.
3. Register `/health`.
4. Add API prefix support for `/api/v1`.

Acceptance criteria:
- `GET /health` returns `{ "status": "ok", "service": "networkpilot-api" }`.
- App runs with Uvicorn.
- Route structure supports future routers.

Testing steps:
- Run backend locally.
- Call `/health`.

Do not touch:
- Do not add auth middleware yet.
- Do not add business endpoints yet.

Depends on:
- Ticket 3

---

### Ticket 10: Add Backend Config and Environment Loading

Goal:
Add typed backend settings.

Context:
Backend needs safe config handling for database, Supabase, CORS, environment, and logging.

Files likely affected:

```text
/backend/app/core/config.py
/backend/.env.example
/backend/app/main.py
```

Implementation steps:
1. Add Pydantic settings.
2. Define required env vars.
3. Add environment-specific behavior for test/dev/prod.
4. Update `.env.example`.

Acceptance criteria:
- Missing required env vars fail clearly outside test mode.
- Settings include database URL, Supabase config, CORS origins, environment, and log level.
- No secrets are printed.

Testing steps:
- Run backend with valid `.env`.
- Run backend without required env and confirm clear failure.

Do not touch:
- Do not store secrets in code.
- Do not use frontend Supabase anon key as backend secret unless intended for public frontend use.

Depends on:
- Ticket 9

---

### Ticket 11: Add CORS, Error Format, and Logging

Goal:
Add standardized API errors, CORS, and basic structured logging.

Context:
The API spec requires consistent error responses and auth-protected clients.

Files likely affected:

```text
/backend/app/main.py
/backend/app/core/errors.py
/backend/app/core/logging.py
/backend/app/schemas/common.py
```

Implementation steps:
1. Add CORS using allowed origins from config.
2. Create custom app errors.
3. Add global exception handlers.
4. Add basic request logging.

Acceptance criteria:
- Errors follow `{ error: { code, message, details } }`.
- CORS allows configured frontend and extension origins.
- Unexpected errors return `INTERNAL_ERROR` without leaking stack traces.

Testing steps:
- Trigger validation error.
- Trigger unknown route.
- Confirm response shape.

Do not touch:
- Do not log auth tokens.
- Do not log private message bodies.

Depends on:
- Ticket 10

---

## Phase 4: Authentication and Authorization

### Ticket 12: Implement Supabase JWT Verification

Goal:
Verify Supabase access tokens on backend requests.

Context:
All endpoints except health require authentication.

Files likely affected:

```text
/backend/app/core/security.py
/backend/app/api/deps.py
/backend/app/api/routes/me.py
```

Implementation steps:
1. Parse `Authorization: Bearer <token>`.
2. Verify Supabase JWT.
3. Extract Supabase user ID and email.
4. Return 401 for missing or invalid token.

Acceptance criteria:
- Valid token resolves current auth claims.
- Missing token returns 401.
- Invalid token returns 401.
- `/health` remains unauthenticated.

Testing steps:
- Call protected test route without token.
- Call with invalid token.
- Call with valid Supabase session token.

Do not touch:
- Do not build custom password auth.
- Do not store Supabase service role key in frontend or extension.

Depends on:
- Ticket 11

---

### Ticket 13: Implement Current User Bootstrap

Goal:
Create or update internal `app_users` and `user_settings` from Supabase claims.

Context:
Supabase Auth stores identity, but the app needs internal user records.

Files likely affected:

```text
/backend/app/services/user_service.py
/backend/app/api/routes/me.py
/backend/app/schemas/users.py
/backend/app/api/router.py
```

Implementation steps:
1. Add user service.
2. Create `app_users` record on first authenticated request.
3. Create default user settings.
4. Implement `GET /me`.

Acceptance criteria:
- First request creates internal user.
- Repeated requests reuse same user.
- `/me` returns user and workspace memberships.
- Email updates are handled safely.

Testing steps:
- Call `/me` with valid token.
- Confirm row exists in `app_users`.
- Call `/me` again and confirm no duplicate row.

Do not touch:
- Do not create a workspace automatically unless explicitly included in this ticket.
- Do not expose Supabase raw JWT claims in response.

Depends on:
- Ticket 12

---

### Ticket 14: Implement Workspace Access Dependencies

Goal:
Add reusable workspace authorization checks.

Context:
Every workspace-scoped query must verify membership.

Files likely affected:

```text
/backend/app/api/deps.py
/backend/app/services/workspace_service.py
/backend/app/models/workspace.py
```

Implementation steps:
1. Add `require_workspace_access`.
2. Add `require_workspace_owner`.
3. Ensure deleted memberships are ignored.
4. Ensure all checks filter by `workspace_id`.

Acceptance criteria:
- Member can access workspace.
- Non-member gets 403.
- Owner-only helper works.
- Deleted membership does not grant access.

Testing steps:
- Create two users and one workspace.
- Test member and non-member access.
- Test owner-only endpoint.

Do not touch:
- Do not trust `workspace_id` without membership check.
- Do not implement full member invitation UI yet.

Depends on:
- Ticket 13

---

### Ticket 15: Implement Workspace Routes

Goal:
Create workspace create, list, and update APIs.

Context:
V1 supports owner/member workspaces for the user and friends.

Files likely affected:

```text
/backend/app/api/routes/workspaces.py
/backend/app/schemas/workspaces.py
/backend/app/services/workspace_service.py
/backend/app/api/router.py
```

Implementation steps:
1. Implement `GET /workspaces`.
2. Implement `POST /workspaces`.
3. Implement `PATCH /workspaces/{workspace_id}` for owner.
4. Create owner membership when workspace is created.

Acceptance criteria:
- User can create workspace.
- Creator becomes owner.
- User can list own workspaces.
- Owner can update defaults and timezone.
- Non-owner cannot update workspace.

Testing steps:
- Create workspace.
- List workspaces.
- Patch workspace settings.
- Try patching as non-owner.

Do not touch:
- Do not build member invitation flow yet.
- Do not seed people or test data here.

Depends on:
- Ticket 14

---

## Phase 5: Core Backend Domain Logic

### Ticket 16: Implement LinkedIn URL Normalizer

Goal:
Normalize and validate LinkedIn profile URLs.

Context:
URL normalization prevents duplicate records and rejects non-profile pages.

Files likely affected:

```text
/backend/app/services/url_normalizer.py
/backend/app/tests/unit/test_url_normalizer.py
```

Implementation steps:
1. Accept raw LinkedIn URL.
2. Strip query params and fragments.
3. Normalize domain and `/in/{slug}` path.
4. Reject company, jobs, feed, search, and non-LinkedIn URLs.

Acceptance criteria:
- `https://www.linkedin.com/in/abc/?utm_source=x` becomes `linkedin.com/in/abc`.
- Profile slug is extracted.
- Invalid LinkedIn pages return validation error.
- Non-LinkedIn URLs are rejected.

Testing steps:
- Run unit tests for valid profile URLs.
- Run unit tests for invalid URLs.
- Test duplicate equivalent URLs.

Do not touch:
- Do not scrape LinkedIn DOM.
- Do not support bulk profile extraction.

Depends on:
- Ticket 11

---

### Ticket 17: Implement People Schemas

Goal:
Add Pydantic schemas for people APIs.

Context:
People are the core CRM records.

Files likely affected:

```text
/backend/app/schemas/people.py
/backend/app/schemas/common.py
```

Implementation steps:
1. Add create, update, response, and list schemas.
2. Add enum-like validation for priority, stage, status, and next action type.
3. Add pagination schema.
4. Add filters schema.

Acceptance criteria:
- Required fields are enforced.
- Priority only accepts A/B/C.
- Tags are limited.
- Response schema matches API spec.

Testing steps:
- Run schema validation tests.
- Try invalid priority.
- Try missing required name.

Do not touch:
- Do not implement database operations in schema files.
- Do not allow frontend to set audit fields.

Depends on:
- Ticket 16

---

### Ticket 18: Implement People Service

Goal:
Add people create, update, get, list, lookup, archive, and soft delete logic.

Context:
This service owns people database behavior.

Files likely affected:

```text
/backend/app/services/people_service.py
/backend/app/models/person.py
/backend/app/services/url_normalizer.py
```

Implementation steps:
1. Implement create with URL normalization.
2. Implement duplicate detection by workspace and normalized URL.
3. Implement list with filters.
4. Implement update for profile fields only.
5. Implement soft delete/archive helpers.

Acceptance criteria:
- Create person saves normalized URL and slug.
- Duplicate normalized URL returns conflict.
- List only returns people from workspace.
- Deleted people are excluded by default.
- Update cannot directly perform stage transitions.

Testing steps:
- Create person.
- Create duplicate person.
- List by workspace.
- Update role/company.
- Soft delete person.

Do not touch:
- Do not update stage transition rules here.
- Do not hard delete people.

Depends on:
- Ticket 17

---

### Ticket 19: Implement People Routes

Goal:
Expose people APIs.

Context:
People routes are used by web app and manually created records.

Files likely affected:

```text
/backend/app/api/routes/people.py
/backend/app/api/router.py
```

Implementation steps:
1. Add `GET /people`.
2. Add `POST /people`.
3. Add `GET /people/{person_id}`.
4. Add `PATCH /people/{person_id}`.
5. Add `DELETE /people/{person_id}`.

Acceptance criteria:
- Routes match API spec.
- Auth is required.
- Workspace access is enforced.
- Error responses use standard format.

Testing steps:
- Create person through API.
- List people.
- Update person.
- Delete person.
- Try accessing another workspace’s person.

Do not touch:
- Do not add extension quick actions here.
- Do not skip authorization checks.

Depends on:
- Ticket 18

---

### Ticket 20: Implement Stage Transition Service

Goal:
Centralize action-to-stage and next-action rules.

Context:
All action transitions must go through one service so web and extension behavior stays consistent.

Files likely affected:

```text
/backend/app/services/transition_service.py
/backend/app/tests/unit/test_transition_service.py
```

Implementation steps:
1. Define V1 action types.
2. Map actions to new stage, next action type, and due date logic.
3. Use workspace default delays.
4. Support override next action date/type.
5. Return transition result object.

Acceptance criteria:
- `invite_sent` sets invite pending and acceptance check date.
- `accepted` sets accepted/no-message and send-first-message next action.
- `message_sent` sets waiting for reply and follow-up 1 due.
- `follow_up_1_sent` sets follow-up 2 due.
- `reply_received` stops generic follow-up sequence.
- Invalid transitions return clear error.

Testing steps:
- Run transition matrix tests.
- Test workspace default delays.
- Test overrides.
- Test invalid action.

Do not touch:
- Do not write database changes in this service.
- Do not add AI message generation.

Depends on:
- Ticket 15

---

### Ticket 21: Implement Activity Schemas

Goal:
Add Pydantic schemas for activities.

Context:
Activities preserve the relationship timeline and trigger transitions.

Files likely affected:

```text
/backend/app/schemas/activities.py
```

Implementation steps:
1. Add create activity schema.
2. Add activity response schema.
3. Add validation for source and action type.
4. Add field limits for message and notes.

Acceptance criteria:
- `action_type` is required.
- `source` must be `web_app`, `chrome_extension`, or `system`.
- Message and notes length limits are enforced.
- Response includes actor info.

Testing steps:
- Validate valid activity.
- Validate invalid action type.
- Validate oversized notes.

Do not touch:
- Do not implement transition rules here.
- Do not expose internal audit-only fields for write.

Depends on:
- Ticket 20

---

### Ticket 22: Implement Activity Service

Goal:
Create activities and update person state in one transaction.

Context:
Activity log plus current state is the core tracking model.

Files likely affected:

```text
/backend/app/services/activity_service.py
/backend/app/services/transition_service.py
/backend/app/models/activity.py
/backend/app/models/person.py
```

Implementation steps:
1. Load person with workspace check.
2. Capture previous stage.
3. Call transition service.
4. Create activity row.
5. Update person state.
6. Commit in one transaction.

Acceptance criteria:
- Activity is created.
- Person stage and next action are updated.
- Previous and new stages are stored.
- Rollback happens if transition fails.
- Actor user is stored.

Testing steps:
- Create activity.
- Verify person state changed.
- Simulate invalid transition and confirm no partial update.

Do not touch:
- Do not allow frontend to directly mutate transition fields through activities.
- Do not skip transaction boundary.

Depends on:
- Ticket 21

---

### Ticket 23: Implement Activity Routes

Goal:
Expose activity list and create endpoints.

Context:
Person detail and quick actions need timeline APIs.

Files likely affected:

```text
/backend/app/api/routes/activities.py
/backend/app/api/router.py
```

Implementation steps:
1. Add `GET /people/{person_id}/activities`.
2. Add `POST /people/{person_id}/activities`.
3. Enforce workspace membership through person lookup.
4. Return updated person with created activity on create.

Acceptance criteria:
- Activities list in newest-first order.
- Create activity applies transition.
- Person outside workspace returns 404 or 403.
- Standard error format is used.

Testing steps:
- Create person.
- Post activity.
- Fetch activity timeline.
- Test unauthorized workspace access.

Do not touch:
- Do not build dashboard queries here.
- Do not hard delete activities.

Depends on:
- Ticket 22

---

### Ticket 24: Implement Snooze and Archive Actions

Goal:
Add fast action endpoints for snooze and archive.

Context:
Snooze and archive prevent the dashboard from becoming noisy.

Files likely affected:

```text
/backend/app/api/routes/people.py
/backend/app/services/people_service.py
/backend/app/services/activity_service.py
/backend/app/schemas/people.py
```

Implementation steps:
1. Add `POST /people/{person_id}/snooze`.
2. Add `POST /people/{person_id}/archive`.
3. Create activity record for each action.
4. Update next action date or archived state.

Acceptance criteria:
- Snooze updates `next_action_date`.
- Snooze creates activity.
- Archive sets status/stage to archived.
- Archive clears next action.
- Archived people disappear from due dashboard.

Testing steps:
- Snooze person and verify next date.
- Archive person and verify status.
- Fetch dashboard due list and confirm archived person is excluded.

Do not touch:
- Do not hard delete people.
- Do not remove existing activities.

Depends on:
- Ticket 23

---

## Phase 6: Dashboard, Templates, and Calendar Link

### Ticket 25: Implement Dashboard Service

Goal:
Add dashboard summary and due follow-up queries.

Context:
The core product answers who should be followed up with today, why, and what to say.

Files likely affected:

```text
/backend/app/services/dashboard_service.py
/backend/app/schemas/dashboard.py
```

Implementation steps:
1. Query due today.
2. Query overdue.
3. Query accepted but not messaged.
4. Query waiting for reply.
5. Add summary count method.

Acceptance criteria:
- Due today includes active people with due date equal to selected date.
- Overdue includes active people with due date before selected date.
- Archived/deleted people are excluded.
- Priority filter works.
- Counts match list queries.

Testing steps:
- Seed people across stages and dates.
- Test due today.
- Test overdue.
- Test archived exclusion.

Do not touch:
- Do not create background jobs.
- Do not generate calendar events here.

Depends on:
- Ticket 24

---

### Ticket 26: Implement Dashboard Routes

Goal:
Expose dashboard summary and due APIs.

Context:
Web dashboard depends on these APIs.

Files likely affected:

```text
/backend/app/api/routes/dashboard.py
/backend/app/api/router.py
```

Implementation steps:
1. Add `GET /dashboard/summary`.
2. Add `GET /dashboard/due`.
3. Accept workspace, date, include overdue, and priority params.
4. Enforce workspace access.

Acceptance criteria:
- Routes match API spec.
- Dashboard summary returns correct counts.
- Dashboard due returns people cards.
- Auth and workspace access are enforced.

Testing steps:
- Call routes with valid workspace.
- Call with unauthorized workspace.
- Call with date and priority filters.

Do not touch:
- Do not return deleted records.
- Do not add analytics V2 metrics.

Depends on:
- Ticket 25

---

### Ticket 27: Implement Template Service

Goal:
Add message template CRUD and default template seeding.

Context:
V1 uses static templates, not paid AI APIs.

Files likely affected:

```text
/backend/app/services/template_service.py
/backend/app/schemas/templates.py
/backend/app/services/workspace_service.py
```

Implementation steps:
1. Implement list/create/update/delete templates.
2. Block duplicate template names per workspace.
3. Seed default templates when workspace is created.
4. Add basic variable preview support.

Acceptance criteria:
- Templates can be listed by workspace and category.
- Create/update/delete works.
- Duplicate active name returns conflict.
- Workspace creation seeds default templates.

Testing steps:
- Create workspace.
- Confirm default templates exist.
- Create custom template.
- Update and delete template.

Do not touch:
- Do not call any AI API.
- Do not support advanced personalization yet.

Depends on:
- Ticket 15

---

### Ticket 28: Implement Template Routes

Goal:
Expose template endpoints.

Context:
Web and extension need template list and copy support.

Files likely affected:

```text
/backend/app/api/routes/templates.py
/backend/app/api/router.py
```

Implementation steps:
1. Add `GET /templates`.
2. Add `POST /templates`.
3. Add `PATCH /templates/{template_id}`.
4. Add `DELETE /templates/{template_id}`.
5. Enforce workspace access.

Acceptance criteria:
- Routes match API spec.
- Auth is required.
- Members can view templates.
- Create/update/delete uses workspace checks.
- Soft delete works.

Testing steps:
- List templates.
- Create template.
- Update template.
- Delete template.
- Try access from another workspace.

Do not touch:
- Do not implement template folders or versioning.
- Do not add AI drafting.

Depends on:
- Ticket 27

---

### Ticket 29: Implement Calendar Reminder Link Endpoint

Goal:
Generate a Google Calendar URL for a daily reminder.

Context:
V1 uses generated calendar links, not Google Calendar OAuth.

Files likely affected:

```text
/backend/app/services/calendar_link_service.py
/backend/app/api/routes/calendar.py
/backend/app/schemas/calendar.py
/backend/app/api/router.py
```

Implementation steps:
1. Add service to build Google Calendar render URL.
2. Add `GET /calendar/daily-reminder-link`.
3. Include dashboard link, title, time, and timezone.
4. Enforce workspace access.

Acceptance criteria:
- Endpoint returns a valid calendar URL.
- No OAuth is required.
- URL includes recurring daily reminder intent.
- Dashboard URL is included in description.

Testing steps:
- Call endpoint.
- Open returned URL manually.
- Confirm title and description appear.

Do not touch:
- Do not store Google refresh tokens.
- Do not create individual per-person calendar events.

Depends on:
- Ticket 26

---

## Phase 7: Extension Backend Endpoints

### Ticket 30: Implement Extension Lookup Endpoint

Goal:
Let the extension check whether the current LinkedIn profile already exists.

Context:
The extension reads the current tab URL, sends it to the backend, and gets either an existing person or a new-profile response.

Files likely affected:

```text
/backend/app/api/routes/extension.py
/backend/app/schemas/extension.py
/backend/app/services/people_service.py
/backend/app/api/router.py
```

Implementation steps:
1. Add `GET /extension/lookup`.
2. Normalize provided LinkedIn URL.
3. Return found person if present.
4. Return normalized URL and slug if not found.
5. Return validation error for invalid page.

Acceptance criteria:
- Existing person returns `found: true`.
- New profile returns `found: false`.
- Non-profile URL returns 422.
- Lookup is scoped to workspace.

Testing steps:
- Lookup saved profile.
- Lookup unsaved profile.
- Lookup LinkedIn company page.
- Lookup another workspace’s profile.

Do not touch:
- Do not scrape LinkedIn.
- Do not auto-create records on lookup.

Depends on:
- Ticket 19

---

### Ticket 31: Implement Extension Quick Create

Goal:
Let the extension create a person with an initial action.

Context:
New profile view needs one save action for invite sent, saved for later, already connected, or message sent.

Files likely affected:

```text
/backend/app/api/routes/extension.py
/backend/app/schemas/extension.py
/backend/app/services/people_service.py
/backend/app/services/activity_service.py
```

Implementation steps:
1. Add `POST /extension/quick-create`.
2. Validate profile URL.
3. Create person.
4. Create initial activity.
5. Return person state and next action.

Acceptance criteria:
- Quick create creates person.
- Initial action creates activity.
- Duplicate URL returns conflict with existing person info.
- Next action is calculated correctly.

Testing steps:
- Quick create with `invite_sent`.
- Quick create with `saved_for_later`.
- Try duplicate URL.
- Inspect activities.

Do not touch:
- Do not send LinkedIn connection requests.
- Do not infer action automatically.

Depends on:
- Ticket 30

---

### Ticket 32: Implement Extension Quick Action

Goal:
Let the extension apply a manual action to an existing person.

Context:
Existing profile view needs buttons for accepted, message sent, follow-up sent, reply received, snooze, archive, and note.

Files likely affected:

```text
/backend/app/api/routes/extension.py
/backend/app/schemas/extension.py
/backend/app/services/activity_service.py
/backend/app/services/people_service.py
```

Implementation steps:
1. Add `POST /extension/quick-action`.
2. Validate person belongs to workspace.
3. Apply activity or special action.
4. Return updated person and activity.
5. Support optional note and next date override.

Acceptance criteria:
- Accepted action works.
- Message sent action works.
- Follow-up 1 and 2 sent work.
- Reply received works.
- Snooze/archive work or delegate to existing services.
- Response includes updated next action.

Testing steps:
- Apply actions in expected sequence.
- Apply invalid transition.
- Verify activity timeline.
- Verify dashboard due dates.

Do not touch:
- Do not auto-message.
- Do not read LinkedIn inbox.
- Do not run background LinkedIn monitoring.

Depends on:
- Ticket 31

---

## Phase 8: Web Frontend Foundation

### Ticket 33: Initialize React Web App

Goal:
Create Vite React TypeScript web app.

Context:
Web app is the main dashboard for due follow-ups, people, templates, and settings.

Files likely affected:

```text
/frontend/package.json
/frontend/index.html
/frontend/src/main.tsx
/frontend/src/app/App.tsx
/frontend/src/app/routes.tsx
/frontend/vite.config.ts
```

Implementation steps:
1. Create Vite React TypeScript app.
2. Add React Router.
3. Add base app shell.
4. Add Tailwind if using Tailwind.

Acceptance criteria:
- Frontend runs locally.
- Root route renders.
- Build succeeds.

Testing steps:
- Run `npm install`.
- Run `npm run dev`.
- Run `npm run build`.

Do not touch:
- Do not implement pages yet.
- Do not add backend calls yet.

Depends on:
- Ticket 3

---

### Ticket 34: Add Frontend Auth Flow

Goal:
Implement Supabase login, logout, session handling, and protected routes.

Context:
Frontend uses Supabase JS client for auth session handling only.

Files likely affected:

```text
/frontend/src/auth/supabaseClient.ts
/frontend/src/auth/LoginPage.tsx
/frontend/src/auth/RequireAuth.tsx
/frontend/src/hooks/useAuth.ts
/frontend/src/app/routes.tsx
```

Implementation steps:
1. Configure Supabase client.
2. Build login/signup form.
3. Add logout.
4. Add protected route wrapper.
5. Redirect authenticated users to dashboard.

Acceptance criteria:
- Unauthenticated users go to `/login`.
- Authenticated users can access protected pages.
- Logout clears session.
- Access token is available for API calls.

Testing steps:
- Sign up or log in.
- Refresh page and confirm session persists.
- Logout and confirm redirect.

Do not touch:
- Do not build custom auth.
- Do not store service role key in frontend.

Depends on:
- Ticket 33

---

### Ticket 35: Add Frontend API Client

Goal:
Add central typed HTTP client.

Context:
Frontend API calls should attach auth token and normalize errors.

Files likely affected:

```text
/frontend/src/api/httpClient.ts
/frontend/src/api/workspacesApi.ts
/frontend/src/api/peopleApi.ts
/frontend/src/api/activitiesApi.ts
/frontend/src/api/dashboardApi.ts
/frontend/src/api/templatesApi.ts
/frontend/src/api/calendarApi.ts
/frontend/src/types/api.ts
```

Implementation steps:
1. Create `httpClient`.
2. Attach Supabase access token.
3. Normalize API errors.
4. Handle 401 by redirecting to login.
5. Add typed endpoint wrappers.

Acceptance criteria:
- API client attaches bearer token.
- JSON responses parse correctly.
- Error shape is normalized.
- 401 redirects or triggers logout.

Testing steps:
- Call `/me`.
- Simulate 401.
- Simulate validation error.

Do not touch:
- Do not duplicate fetch logic inside pages.
- Do not expose tokens in logs.

Depends on:
- Ticket 34

---

### Ticket 36: Build App Layout and Navigation

Goal:
Create shared app shell with navigation.

Context:
Web pages need consistent layout.

Files likely affected:

```text
/frontend/src/components/layout/AppLayout.tsx
/frontend/src/components/layout/Sidebar.tsx
/frontend/src/components/layout/Topbar.tsx
/frontend/src/app/routes.tsx
```

Implementation steps:
1. Add sidebar/topbar.
2. Add nav links for dashboard, people, templates, settings.
3. Show current user and workspace.
4. Add responsive behavior.

Acceptance criteria:
- Navigation works.
- Protected pages render inside layout.
- Current workspace is visible.
- 404 route works.

Testing steps:
- Navigate between pages.
- Refresh on nested route.
- Test mobile-ish viewport.

Do not touch:
- Do not build page business logic here.
- Do not add complex theming.

Depends on:
- Ticket 35

---

### Ticket 37: Add Shared UI Components

Goal:
Add reusable UI primitives.

Context:
The frontend plan calls for shared buttons, inputs, modals, badges, skeletons, alerts, and empty states.

Files likely affected:

```text
/frontend/src/components/common/Button.tsx
/frontend/src/components/common/Input.tsx
/frontend/src/components/common/Textarea.tsx
/frontend/src/components/common/Select.tsx
/frontend/src/components/common/Modal.tsx
/frontend/src/components/common/Toast.tsx
/frontend/src/components/common/Badge.tsx
/frontend/src/components/common/Skeleton.tsx
/frontend/src/components/common/ErrorAlert.tsx
/frontend/src/components/common/EmptyState.tsx
/frontend/src/components/common/ConfirmDialog.tsx
```

Implementation steps:
1. Add basic UI components.
2. Add simple styling.
3. Add TypeScript props.
4. Export components from index file.

Acceptance criteria:
- Components compile.
- Components are reusable.
- Components do not contain business-specific logic.

Testing steps:
- Render components in a temporary dev page if available.
- Run build.

Do not touch:
- Do not add a large component library unless already chosen.
- Do not hardcode page-specific API calls.

Depends on:
- Ticket 36

---

## Phase 9: Web Frontend Features

### Ticket 38: Build Dashboard Page

Goal:
Show due follow-ups and quick actions.

Context:
Dashboard is the main daily workflow.

Files likely affected:

```text
/frontend/src/pages/DashboardPage.tsx
/frontend/src/components/people/DuePersonCard.tsx
/frontend/src/components/people/QuickActionMenu.tsx
/frontend/src/components/people/SnoozeModal.tsx
/frontend/src/components/people/ArchiveDialog.tsx
```

Implementation steps:
1. Fetch dashboard summary.
2. Fetch due and overdue people.
3. Render summary cards.
4. Add quick actions.
5. Add loading, empty, and error states.

Acceptance criteria:
- Dashboard shows due today.
- Overdue people are visible.
- Quick actions update person and refresh list.
- Empty state shows when no due follow-ups exist.
- Errors show retry option.

Testing steps:
- Seed due people.
- Mark follow-up sent.
- Snooze person.
- Archive person.
- Confirm list refreshes.

Do not touch:
- Do not build people list filters here.
- Do not add analytics charts.

Depends on:
- Ticket 26
- Ticket 37

---

### Ticket 39: Build People List Page

Goal:
Create searchable/filterable people table.

Context:
Users need a full CRM view beyond today’s due follow-ups.

Files likely affected:

```text
/frontend/src/pages/PeopleListPage.tsx
/frontend/src/components/people/PeopleFilters.tsx
/frontend/src/components/people/PeopleTable.tsx
/frontend/src/components/people/PersonTableRow.tsx
/frontend/src/components/people/StageBadge.tsx
/frontend/src/components/people/PriorityBadge.tsx
/frontend/src/components/people/NextActionBadge.tsx
```

Implementation steps:
1. Fetch people list.
2. Add search input.
3. Add filters for stage, priority, status, and due status.
4. Add pagination controls.
5. Add open profile and archive actions.

Acceptance criteria:
- People list loads.
- Search works.
- Filters work.
- Row click opens person detail.
- LinkedIn profile link opens in a new tab.

Testing steps:
- Create multiple people.
- Search by name/company.
- Filter by priority and stage.
- Archive a person.

Do not touch:
- Do not implement activity timeline here.
- Do not add CSV import.

Depends on:
- Ticket 19
- Ticket 37

---

### Ticket 40: Build Person Detail Page

Goal:
Show and edit one person with activity timeline.

Context:
Person detail is where full context and history live.

Files likely affected:

```text
/frontend/src/pages/PersonDetailPage.tsx
/frontend/src/components/people/PersonHeader.tsx
/frontend/src/components/people/PersonProfileForm.tsx
/frontend/src/components/people/StagePanel.tsx
/frontend/src/components/people/NextActionPanel.tsx
/frontend/src/components/people/QuickActionPanel.tsx
/frontend/src/components/activities/ActivityTimeline.tsx
/frontend/src/components/activities/AddActivityForm.tsx
```

Implementation steps:
1. Fetch person details.
2. Fetch activities.
3. Render profile summary and timeline.
4. Add profile edit form.
5. Add action logging form.
6. Add snooze/archive actions.

Acceptance criteria:
- Person details load.
- Activity timeline loads.
- Profile fields can be edited.
- Manual action can be logged.
- Timeline refreshes after action.
- Loading, empty, and error states exist.

Testing steps:
- Open person detail.
- Edit role/company.
- Log follow-up.
- Add note.
- Confirm activity appears.

Do not touch:
- Do not allow direct stage mutation from profile edit form.
- Do not add LinkedIn scraping.

Depends on:
- Ticket 23
- Ticket 39

---

### Ticket 41: Build Templates Page

Goal:
Manage reusable message templates.

Context:
V1 uses static templates with copy support.

Files likely affected:

```text
/frontend/src/pages/TemplatesPage.tsx
/frontend/src/components/templates/TemplateList.tsx
/frontend/src/components/templates/TemplateEditor.tsx
/frontend/src/components/templates/TemplatePreview.tsx
/frontend/src/components/templates/TemplateVariablePreview.tsx
/frontend/src/components/templates/TemplateCopyButton.tsx
```

Implementation steps:
1. Fetch templates.
2. Add create/edit/delete forms.
3. Add template preview.
4. Add copy-to-clipboard button.
5. Show supported variables.

Acceptance criteria:
- Templates list loads.
- Template can be created.
- Template can be edited.
- Template can be soft-deleted.
- Copy button works.
- Empty state exists.

Testing steps:
- Create new template.
- Edit body.
- Copy text.
- Delete template.
- Refresh page.

Do not touch:
- Do not add AI generation.
- Do not add template analytics.

Depends on:
- Ticket 28
- Ticket 37

---

### Ticket 42: Build Settings Page

Goal:
Manage workspace defaults and daily calendar reminder link.

Context:
Settings include timezone, default follow-up delays, acceptance check delay, daily reminder time, and generated Google Calendar link.

Files likely affected:

```text
/frontend/src/pages/SettingsPage.tsx
/frontend/src/components/settings/WorkspaceSettingsForm.tsx
/frontend/src/components/settings/ReminderSettingsForm.tsx
/frontend/src/components/settings/CalendarReminderLinkCard.tsx
```

Implementation steps:
1. Fetch current workspace.
2. Add workspace settings form.
3. Add reminder settings form.
4. Fetch generated calendar link.
5. Add copy/open calendar link action.

Acceptance criteria:
- Workspace name can be updated.
- Timezone can be updated.
- Follow-up delays can be updated.
- Calendar reminder link is generated.
- Validation prevents invalid delay values.

Testing steps:
- Update workspace name.
- Update default follow-up days.
- Generate calendar link.
- Open calendar link.

Do not touch:
- Do not implement Google OAuth.
- Do not create per-person calendar events.

Depends on:
- Ticket 29
- Ticket 36

---

## Phase 10: Chrome Extension Foundation

### Ticket 43: Initialize Chrome Extension App

Goal:
Create React MV3 Chrome extension.

Context:
Extension is the fast capture/update interface while browsing LinkedIn.

Files likely affected:

```text
/extension/package.json
/extension/manifest.json
/extension/vite.config.ts
/extension/src/popup/PopupApp.tsx
/extension/src/background/serviceWorker.ts
```

Implementation steps:
1. Set up React TypeScript extension app.
2. Add Manifest V3.
3. Add popup entry.
4. Add minimal service worker.
5. Configure build output.

Acceptance criteria:
- Extension builds.
- Chrome can load unpacked build.
- Popup opens.
- Manifest requests minimal permissions.

Testing steps:
- Run build.
- Load unpacked extension in Chrome.
- Open popup.

Do not touch:
- Do not request `<all_urls>`.
- Do not inject visible UI into LinkedIn.
- Do not add content scripts unless explicitly needed.

Depends on:
- Ticket 3

---

### Ticket 44: Implement Extension Token Storage

Goal:
Store API base URL and user token in Chrome storage.

Context:
V1 can use simple token paste/connect flow.

Files likely affected:

```text
/extension/src/auth/tokenStorage.ts
/extension/src/popup/UnauthenticatedView.tsx
/extension/src/api/extensionApi.ts
```

Implementation steps:
1. Add token read/write helpers using `chrome.storage`.
2. Add unauthenticated view.
3. Add API base URL config field.
4. Add clear token action.

Acceptance criteria:
- Token can be saved.
- Token can be loaded after popup reopen.
- Token can be cleared.
- API client reads token from storage.

Testing steps:
- Save token.
- Close and reopen popup.
- Clear token.
- Confirm unauthenticated view returns.

Do not touch:
- Do not store LinkedIn cookies.
- Do not store LinkedIn password.
- Do not use localStorage for secrets if Chrome storage is available.

Depends on:
- Ticket 43

---

### Ticket 45: Implement Active Tab URL Reader

Goal:
Read current active tab URL and validate LinkedIn profile page locally.

Context:
Extension should show invalid page state when not on a LinkedIn profile.

Files likely affected:

```text
/extension/src/utils/activeTab.ts
/extension/src/utils/normalizeLinkedInUrl.ts
/extension/src/utils/pageTitleParser.ts
/extension/src/popup/InvalidPageView.tsx
```

Implementation steps:
1. Read active tab via Chrome tabs API.
2. Add lightweight local LinkedIn profile URL check.
3. Extract page title for suggested name.
4. Show invalid page message when needed.

Acceptance criteria:
- LinkedIn profile URL is detected.
- Non-LinkedIn page shows invalid page view.
- LinkedIn company/search/feed pages show invalid page view.
- Page title is available to new profile form.

Testing steps:
- Open LinkedIn profile page.
- Open LinkedIn company page.
- Open Google or blank tab.
- Open extension popup.

Do not touch:
- Do not read DOM content.
- Do not scrape profile fields.
- Do not require content script.

Depends on:
- Ticket 44

---

### Ticket 46: Implement Extension API Client

Goal:
Add extension-specific API client.

Context:
Extension needs lookup, quick create, quick action, and template calls.

Files likely affected:

```text
/extension/src/api/extensionApi.ts
/extension/src/types/api.ts
```

Implementation steps:
1. Add fetch wrapper.
2. Attach bearer token.
3. Add lookup API.
4. Add quick create API.
5. Add quick action API.
6. Add template list API.

Acceptance criteria:
- API client attaches auth token.
- Errors are normalized.
- 401 clears token or shows unauthenticated state.
- Base URL is configurable.

Testing steps:
- Call lookup with valid token.
- Call with invalid token.
- Call with bad URL.
- Confirm error UI receives normalized error.

Do not touch:
- Do not duplicate backend transition logic in extension.
- Do not hardcode production API URL only.

Depends on:
- Ticket 44
- Ticket 32

---

## Phase 11: Chrome Extension Features

### Ticket 47: Build Extension Lookup Flow

Goal:
Route popup to unauthenticated, invalid page, new profile, or existing profile view.

Context:
Popup behavior depends on token, current tab, and lookup result.

Files likely affected:

```text
/extension/src/popup/PopupApp.tsx
/extension/src/popup/LoadingView.tsx
/extension/src/popup/ErrorView.tsx
/extension/src/popup/NewProfileView.tsx
/extension/src/popup/ExistingProfileView.tsx
```

Implementation steps:
1. Load token.
2. Read active tab.
3. Validate URL locally.
4. Call lookup API.
5. Render correct view based on response.

Acceptance criteria:
- Missing token shows unauthenticated view.
- Invalid tab shows invalid page view.
- New profile shows new profile form.
- Existing profile shows existing person state.
- Loading and error states work.

Testing steps:
- Test each popup state manually.
- Test network failure.
- Test invalid token.

Do not touch:
- Do not auto-create a person during lookup.
- Do not inject LinkedIn page UI.

Depends on:
- Ticket 46

---

### Ticket 48: Build New Profile Extension View

Goal:
Let user save a new LinkedIn profile with an initial action.

Context:
This is the primary capture flow after sending a manual connection request.

Files likely affected:

```text
/extension/src/popup/NewProfileView.tsx
/extension/src/popup/components/PrioritySelect.tsx
/extension/src/popup/components/InitialActionSelect.tsx
```

Implementation steps:
1. Show name, URL, role, company, location, priority, connection note, and initial action.
2. Prefill name from page title when possible.
3. Call quick create API.
4. Show success confirmation with next action.

Acceptance criteria:
- User can save new profile.
- URL is read-only.
- Initial action is required.
- Priority defaults to B.
- Success view shows next action/date.

Testing steps:
- Save new profile.
- Save with missing name.
- Save duplicate profile.
- Confirm backend activity exists.

Do not touch:
- Do not auto-detect action.
- Do not auto-send connection note.
- Do not scrape profile content.

Depends on:
- Ticket 47

---

### Ticket 49: Build Existing Profile Extension View

Goal:
Let user view existing person context and apply quick actions.

Context:
Existing profile view should reduce manual tracking effort.

Files likely affected:

```text
/extension/src/popup/ExistingProfileView.tsx
/extension/src/popup/ActionButtons.tsx
/extension/src/popup/SnoozeForm.tsx
/extension/src/popup/AddNoteForm.tsx
```

Implementation steps:
1. Display name, company, role, stage, last action, next action, due date, and notes.
2. Add quick action buttons.
3. Add snooze form.
4. Add archive action.
5. Add note action.
6. Show confirmation after success.

Acceptance criteria:
- Existing person context is visible.
- Accepted/message/follow-up/reply actions work.
- Snooze works.
- Archive works.
- Add note works.
- View refreshes after action.

Testing steps:
- Open saved LinkedIn profile.
- Apply accepted action.
- Apply follow-up action.
- Snooze person.
- Archive person.

Do not touch:
- Do not send messages.
- Do not click LinkedIn buttons.
- Do not run background monitoring.

Depends on:
- Ticket 48

---

### Ticket 50: Add Template Copy Panel to Extension

Goal:
Show templates in extension and allow copy-to-clipboard.

Context:
V1 speeds up messaging but keeps final sending manual.

Files likely affected:

```text
/extension/src/popup/TemplateCopyPanel.tsx
/extension/src/utils/templateRender.ts
/extension/src/api/extensionApi.ts
```

Implementation steps:
1. Fetch templates.
2. Render template list.
3. Replace basic variables using current person.
4. Add copy button.
5. Show copied confirmation.

Acceptance criteria:
- Templates load in existing and new profile flows where useful.
- Variables `{{first_name}}`, `{{name}}`, `{{company}}`, and `{{role}}` render.
- Copy button works.
- Empty template state exists.

Testing steps:
- Create template in web app.
- Open extension on saved profile.
- Copy rendered template.
- Paste into text field manually.

Do not touch:
- Do not auto-fill LinkedIn message box.
- Do not send messages.
- Do not add AI drafting.

Depends on:
- Ticket 49
- Ticket 28

---

## Phase 12: Testing and Quality

### Ticket 51: Add Backend Unit Tests

Goal:
Add focused unit tests for risky backend logic.

Context:
URL normalization, transitions, reminders, template rendering, and authorization are high-risk areas.

Files likely affected:

```text
/backend/app/tests/unit/test_url_normalizer.py
/backend/app/tests/unit/test_transition_service.py
/backend/app/tests/unit/test_calendar_link_service.py
/backend/app/tests/unit/test_template_service.py
/backend/app/tests/unit/test_authorization.py
```

Implementation steps:
1. Add pytest setup.
2. Add unit tests for URL normalizer.
3. Add transition matrix tests.
4. Add date calculation tests.
5. Add template rendering tests.

Acceptance criteria:
- Unit tests run with `pytest`.
- Critical transition cases are covered.
- Invalid URL cases are covered.
- Calendar URL generation is covered.

Testing steps:
- Run `pytest backend/app/tests/unit`.
- Confirm all tests pass.

Do not touch:
- Do not require real Supabase project for unit tests.
- Do not test frontend here.

Depends on:
- Ticket 29

---

### Ticket 52: Add Backend Integration Tests

Goal:
Test core API flows against a test database.

Context:
Backend must preserve workspace security and transaction behavior.

Files likely affected:

```text
/backend/app/tests/integration/conftest.py
/backend/app/tests/integration/test_people_api.py
/backend/app/tests/integration/test_activity_api.py
/backend/app/tests/integration/test_dashboard_api.py
/backend/app/tests/integration/test_extension_api.py
```

Implementation steps:
1. Add test database config.
2. Add auth test helper.
3. Test create/list/update people.
4. Test duplicate URL conflict.
5. Test activity transitions.
6. Test dashboard due queries.
7. Test extension quick create/action.

Acceptance criteria:
- Integration tests run against isolated test DB.
- Workspace boundary tests pass.
- Duplicate conflict returns 409.
- Invalid transition returns 400.
- Unauthorized requests return 401/403.

Testing steps:
- Run full backend test suite.
- Run tests twice to catch data leakage.

Do not touch:
- Do not run tests against production database.
- Do not depend on real LinkedIn or Google.

Depends on:
- Ticket 32
- Ticket 51

---

### Ticket 53: Add Frontend Smoke Tests

Goal:
Add basic frontend tests for key screens and states.

Context:
V1 needs confidence that pages render and handle API states.

Files likely affected:

```text
/frontend/src/pages/*.test.tsx
/frontend/src/components/**/*.test.tsx
/frontend/vitest.config.ts
/frontend/src/test/setup.ts
```

Implementation steps:
1. Configure Vitest and React Testing Library.
2. Test login page render.
3. Test dashboard loading/empty/error states.
4. Test people list render.
5. Test template copy button.

Acceptance criteria:
- Frontend test command runs.
- Key pages render without crashing.
- Loading/empty/error states are covered.
- Tests use mocked API calls.

Testing steps:
- Run `npm test`.
- Run `npm run build`.

Do not touch:
- Do not add full E2E browser automation yet.
- Do not require real Supabase login for unit tests.

Depends on:
- Ticket 42

---

### Ticket 54: Add Extension Smoke Tests and Manual QA Checklist

Goal:
Add test coverage and manual QA checklist for extension flows.

Context:
Chrome extension behavior is hard to test fully, so combine lightweight tests with manual checklist.

Files likely affected:

```text
/extension/src/**/*.test.ts
/extension/vitest.config.ts
/docs/EXTENSION_QA.md
```

Implementation steps:
1. Test URL utilities.
2. Test page title parsing.
3. Test template rendering.
4. Add manual QA checklist for Chrome.
5. Document expected popup states.

Acceptance criteria:
- Extension utility tests pass.
- QA doc covers unauthenticated, invalid page, new profile, existing profile, quick action, and template copy.
- Manual steps are clear.

Testing steps:
- Run extension tests.
- Build extension.
- Follow QA checklist manually.

Do not touch:
- Do not add content script tests.
- Do not automate LinkedIn actions.

Depends on:
- Ticket 50

---

## Phase 13: Deployment

### Ticket 55: Prepare Backend for Render Deployment

Goal:
Add production-ready backend deployment config for Render.

Context:
Backend is hosted as a FastAPI service.

Files likely affected:

```text
/backend/Procfile
/backend/render.yaml
/backend/pyproject.toml
/backend/README.md
/backend/app/main.py
```

Implementation steps:
1. Add production start command.
2. Add allowed origins config.
3. Add health check route.
4. Document Render environment variables.
5. Confirm migrations deployment process.

Acceptance criteria:
- Backend can start in production mode.
- `/health` works.
- CORS allows deployed frontend.
- Render env var list is documented.

Testing steps:
- Run production command locally.
- Deploy to Render dev service.
- Call `/health`.

Do not touch:
- Do not commit production secrets.
- Do not run migrations automatically without clear command.

Depends on:
- Ticket 52

---

### Ticket 56: Deploy Backend and Run Migrations

Goal:
Deploy backend and apply database migrations safely.

Context:
Deployment and migrations are risky because they affect shared data.

Files likely affected:

```text
/backend/README.md
/docs/DEPLOYMENT.md
```

Implementation steps:
1. Create Render service.
2. Add environment variables.
3. Deploy backend.
4. Run Alembic migration against Supabase.
5. Verify health and protected routes.

Acceptance criteria:
- Backend is live.
- Migration succeeded.
- `/health` returns ok.
- Protected route returns 401 without token.
- `/me` works with valid token.

Testing steps:
- Call live `/health`.
- Call live `/me` with and without token.
- Inspect Supabase tables.

Do not touch:
- Do not use production database for experiments.
- Do not expose Supabase service role key.

Depends on:
- Ticket 55

---

### Ticket 57: Prepare Frontend for Vercel Deployment

Goal:
Configure web app deployment.

Context:
React web app should deploy to Vercel.

Files likely affected:

```text
/frontend/vercel.json
/frontend/.env.example
/frontend/README.md
/docs/DEPLOYMENT.md
```

Implementation steps:
1. Add Vercel config if needed.
2. Document frontend env vars.
3. Configure API base URL.
4. Configure Supabase frontend variables.
5. Confirm build output.

Acceptance criteria:
- Frontend builds locally.
- Env vars are documented.
- API URL points to deployed backend in production.
- No secrets are bundled.

Testing steps:
- Run `npm run build`.
- Inspect production env vars.
- Deploy preview build.

Do not touch:
- Do not put backend secrets in frontend.
- Do not hardcode local API URL.

Depends on:
- Ticket 42
- Ticket 56

---

### Ticket 58: Deploy Frontend to Vercel

Goal:
Deploy web app and verify auth plus dashboard.

Context:
Vercel hosts the React app.

Files likely affected:

```text
/docs/DEPLOYMENT.md
/frontend/README.md
```

Implementation steps:
1. Connect repo to Vercel.
2. Add environment variables.
3. Deploy.
4. Test login.
5. Test API calls to backend.

Acceptance criteria:
- Frontend is live.
- Login works.
- Dashboard loads after login.
- People/templates/settings routes render.
- API calls hit deployed backend.

Testing steps:
- Visit deployed URL.
- Log in.
- Create workspace.
- Navigate all pages.

Do not touch:
- Do not disable auth to make deployment easier.
- Do not bypass backend API with direct Supabase database access.

Depends on:
- Ticket 57

---

### Ticket 59: Build Extension Release Package

Goal:
Create a loadable extension package for local Chrome use.

Context:
V1 extension can be used as an unpacked extension before Chrome Web Store.

Files likely affected:

```text
/extension/package.json
/extension/README.md
/docs/EXTENSION_INSTALL.md
```

Implementation steps:
1. Add production build command.
2. Add install instructions.
3. Document required API base URL.
4. Build extension.
5. Verify manifest and output folder.

Acceptance criteria:
- Extension builds successfully.
- Output can be loaded as unpacked extension.
- Install doc explains setup.
- Extension points to correct backend API.

Testing steps:
- Run extension build.
- Load unpacked in Chrome.
- Open LinkedIn profile.
- Verify lookup flow.

Do not touch:
- Do not publish to Chrome Web Store yet.
- Do not add broad permissions.

Depends on:
- Ticket 54
- Ticket 56

---

## Phase 14: End-to-End V1 Validation

### Ticket 60: Run Full Manual V1 User Flow

Goal:
Validate the complete product from login to LinkedIn tracking.

Context:
This checks that V1 solves the original workflow.

Files likely affected:

```text
/docs/QA_RESULTS.md
/docs/BUGS_FOUND.md
```

Implementation steps:
1. Log into web app.
2. Create workspace.
3. Install extension.
4. Open LinkedIn profile.
5. Save new person as invite sent.
6. Mark accepted.
7. Send first message manually and mark message sent.
8. Verify dashboard due follow-up.
9. Snooze and archive.
10. Copy template.

Acceptance criteria:
- User can complete full tracking flow.
- Dashboard updates correctly.
- Extension and web app show same person state.
- Activity timeline is accurate.
- No automatic LinkedIn messaging occurs.

Testing steps:
- Follow full flow with at least three test profiles.
- Test duplicate URL.
- Test invalid LinkedIn page.
- Test overdue follow-up.

Do not touch:
- Do not use real high-volume outreach during QA.
- Do not enable any automation that clicks or sends on LinkedIn.

Depends on:
- Ticket 58
- Ticket 59

---

### Ticket 61: Fix Critical V1 Bugs Only

Goal:
Fix only bugs found during full manual QA.

Context:
This ticket prevents scope creep before V1 launch.

Files likely affected:

```text
/backend
/frontend
/extension
/docs/BUGS_FOUND.md
```

Implementation steps:
1. Review QA bug list.
2. Categorize bugs as critical, important, or later.
3. Fix critical blockers.
4. Retest affected flows.
5. Update bug list.

Acceptance criteria:
- No blocker prevents login, profile save, lookup, quick action, dashboard due, template copy, or deployment.
- Fixed bugs have test notes.
- Non-critical issues are moved to V2/backlog.

Testing steps:
- Retest only changed areas.
- Rerun backend/frontend/extension tests.
- Repeat full V1 flow once.

Do not touch:
- Do not add new features.
- Do not redesign UI.
- Do not introduce Gmail, Google OAuth, AI, or bulk import.

Depends on:
- Ticket 60

---

### Ticket 62: Finalize README and V1 Handoff Docs

Goal:
Create final setup, usage, and deployment documentation.

Context:
The project should be understandable for future coding models and friends.

Files likely affected:

```text
/README.md
/backend/README.md
/frontend/README.md
/extension/README.md
/docs/DEPLOYMENT.md
/docs/EXTENSION_INSTALL.md
/docs/V1_USER_GUIDE.md
```

Implementation steps:
1. Update root README.
2. Add backend setup steps.
3. Add frontend setup steps.
4. Add extension setup steps.
5. Add deployment notes.
6. Add simple user guide.

Acceptance criteria:
- New developer can set up project from README.
- User can install extension from docs.
- Deployment steps are documented.
- V1 scope and non-goals are clear.

Testing steps:
- Follow docs from scratch where practical.
- Ask another coding model to review docs for missing steps.

Do not touch:
- Do not change product behavior.
- Do not add future roadmap work into V1 implementation steps.

Depends on:
- Ticket 61

---

## V1 Stop Line

Do not add these before V1 is stable:

- Automatic LinkedIn messaging
- Automatic connection requests
- LinkedIn inbox scraping
- LinkedIn DOM scraping
- LinkedIn page UI injection
- Gmail notification parsing
- Google Calendar OAuth
- Individual calendar reminders for every person
- AI-generated personalized messages
- CSV import/export
- Team invitation UI
- Billing
- Chrome Web Store publishing
- Mobile app

V1 is complete when the user can manually browse LinkedIn, save or update a profile from the Chrome extension, track stages and activity history, see who needs follow-up today, copy templates, snooze/archive people, and use the web dashboard as the source of truth.
