# Repo Context — NetworkPilot CRM — audited 2026-07-12

## Stack

- Root orchestration: npm scripts in `package.json`; root package version is `0.1.0`.
- Web: React 18.2, React Router 6.21, Zustand 4.4, TypeScript 5.3, Vite 5.0, Tailwind CSS and Supabase JS (`frontend/package.json`).
- API: Python 3.11+, FastAPI, Pydantic 2, SQLAlchemy 2 async, asyncpg, Alembic, python-jose and Uvicorn (`backend/pyproject.toml`).
- Extension: React 18, TypeScript 5.3, Vite, CRXJS and Chrome Manifest V3 (`extension/package.json`, `extension/manifest.json`).
- Persistence/auth: Supabase-hosted PostgreSQL and Supabase JWT authentication (`docs/DECISIONS.md`, `backend/app/core/security.py`).
- Hosting: Vercel for the frontend and Render for the backend (`frontend/vercel.json`, `backend/render.yaml`).

## Folder Map

```text
backend/
  app/api/          FastAPI router composition, dependencies and route handlers
  app/core/         configuration, JWT verification, logging and error handlers
  app/db/           async sessions, SQLAlchemy base classes and Alembic migrations
  app/models/       SQLAlchemy entities
  app/schemas/      Pydantic request/response contracts
  app/services/     business logic and database queries
  app/tests/        pytest unit and HTTP integration tests
frontend/
  src/api/          authenticated HTTP client and CSV download helper
  src/app/          route composition
  src/auth/         Supabase client and protected-route wrapper
  src/components/   shared UI and domain components
  src/pages/        route-level React pages
  src/stores/       Zustand auth/workspace stores
  src/test/         Vitest setup
extension/
  src/api/          extension API client
  src/auth/         Supabase and token storage
  src/popup/        popup screens and controls
  src/utils/        tab and template utilities with tests
docs/               product, architecture, contract, QA and operating documents
tests/              root Playwright tests; currently only an example specification
```

No folder inspected is marked legacy. `DEVELOPMENT_BACKLOG.md` is historical V1 planning material; new version tickets must not treat its old scope prohibitions as current contracts.

## Conventions

- Python modules and database fields use `snake_case`; TypeScript components use `PascalCase`, functions/state use `camelCase` (`backend/app/services/people_service.py`, `frontend/src/pages/PeopleListPage.tsx`).
- Backend route handlers are thin: validate through Pydantic/FastAPI, call a service, log masked identifiers, and return schema instances (`backend/app/api/routes/people.py`, `workspaces.py`, `templates.py`).
- Services own business logic and SQLAlchemy queries (`backend/app/services/people_service.py`, `workspace_service.py`, `template_service.py`).
- Models use typed SQLAlchemy `Mapped` columns and shared UUID/timestamp/soft-delete mixins (`backend/app/models/person.py`, `workspace.py`, `template.py`, `backend/app/db/base.py`).
- Frontend pages use named function exports, local TypeScript interfaces, shared controls from `frontend/src/components/common`, and explicit loading/empty/error states (`PeopleListPage.tsx`, `DashboardPage.tsx`, `TemplatesPage.tsx`).
- Tests use `test_*.py` with pytest classes in `backend/app/tests`, and `*.test.tsx` with Vitest/Testing Library in the frontend.
- Logging calls use stable component/module prefixes and masked IDs; do not log tokens, emails, notes, or full profile URLs (`backend/app/core/logging.py`, `frontend/src/utils/logger.ts`).

## Auth

- Requests use `Authorization: Bearer <Supabase access token>` (`backend/app/api/deps.py`).
- `get_current_auth` verifies the JWT with `verify_supabase_token`; `get_current_user` loads or bootstraps `AppUser` (`backend/app/api/deps.py`, `backend/app/core/security.py`).
- Workspace routes use `require_workspace_access`, which reads the current user and verifies active membership (`backend/app/services/workspace_service.py`).
- New workspace-scoped endpoints must accept `workspace_id` at the contract-defined location and use `Depends(require_workspace_access)` or explicitly call it when the ID is in a request body (`backend/app/api/routes/people.py`, `backend/app/api/routes/extension.py`).
- Current membership roles are `owner` and `member`; fine-grained authorization is not yet implemented (`backend/app/models/workspace.py`, `docs/DATABASE_SCHEMA.md`).

## API Style

- Base path: `/api/v1`, composed in `backend/app/api/router.py`.
- Success responses are direct JSON objects/lists, not wrapped in a data envelope.
- Errors use `{ "error": { "code": string, "message": string, "details": object|null } }` through `backend/app/core/errors.py`.
- People pagination returns `{ items: PersonResponse[], total: int, page: int, limit: int }`; limits are 1–100 (`backend/app/api/routes/people.py`, `backend/app/schemas/people.py`).
- Validation uses Pydantic fields plus FastAPI `Query`/`Form` constraints.

Example:

```http
GET /api/v1/people?workspace_id=<uuid>&page=1&limit=20
Authorization: Bearer <token>

200
{
  "items": [{ "id": "<uuid>", "workspace_id": "<uuid>", "name": "Ada Lovelace", "linkedin_url": "linkedin.com/in/ada-lovelace", "priority": "B", "stage": "invite_sent", "status": "active", "is_favorite": false, "favorite_notes": null, "...": "PersonResponse fields" }],
  "total": 1,
  "page": 1,
  "limit": 20
}
```

## Database

- PostgreSQL via SQLAlchemy 2 async and asyncpg (`backend/app/db/session.py`).
- Alembic migrations live in `backend/app/db/migrations/versions`; run from `backend` with `.venv/bin/alembic upgrade head`.
- Entities live in `backend/app/models`; tables/columns use `snake_case`, UUID primary keys, foreign keys and explicit indexes.
- `TimestampMixin` provides `created_at` and `updated_at`; `SoftDeleteMixin` provides nullable `deleted_at` (`backend/app/db/base.py`).
- `get_db` commits once after a successful request and rolls back on exceptions, so multi-step service writes share one request transaction (`backend/app/db/session.py`).
- Existing migration head at audit time: `005_people_favorites`.

## Testing

- Backend: pytest + pytest-asyncio/httpx; SQLite is used by integration fixtures in `backend/app/tests/integration/conftest.py`.
- Full backend suite: `cd backend && .venv/bin/python -m pytest app/tests -q`.
- One backend file: `cd backend && .venv/bin/python -m pytest app/tests/integration/test_people_api.py -q`.
- Frontend: Vitest + Testing Library; full suite `cd frontend && npm test -- --run`; production type/build gate `npm run build`.
- Extension: Vitest; `cd extension && npm test -- --run`; build with `npm run build`.
- Root Playwright is configured in `playwright.config.ts`, but `tests/example.spec.ts` is not meaningful product coverage.
- Shared backend fixtures: `client`, `mock_headers`, test database overrides (`backend/app/tests/integration/conftest.py`).
- SQLite integration tests must map PostgreSQL `ARRAY` columns to SQLAlchemy JSON before `create_all`; compiling the DDL type alone does not provide list bind/result processing (`backend/app/tests/integration/conftest.py`).

## Reusable Utilities

- `backend/app/core/errors.py` → application error taxonomy and safe response shape.
- `backend/app/core/logging.py` → structured logger setup and ID masking.
- `backend/app/services/url_normalizer.py` → canonical LinkedIn profile URL handling.
- `backend/app/services/transition_service.py` → stage/next-action transition rules.
- `backend/app/services/csv_sanitizer.py` → spreadsheet-formula-safe CSV output.
- `backend/app/services/csv_import_service.py` → CSV parsing, validation, duplicate checks and batched commits.
- `backend/app/services/bulk_people_service.py` → atomic explicit-selection People mutations for `v0.0.1`.
- `frontend/src/api/httpClient.ts` → token attachment, base URL normalization, JSON/blob requests and API namespaces.
- `frontend/src/components/common/*` → Button, Input, Select, Textarea, Modal, EmptyState, ErrorAlert and Skeleton.
- `frontend/src/stores/workspaceStore.ts` → workspace loading and active workspace selection.
- `extension/src/utils/activeTab.ts` and `templateRender.ts` → active LinkedIn tab parsing and template interpolation.

## Landmines

- Every ORM field inherited from a mixin must exist in both the initial schema and an upgrade migration; `workspace_members.updated_at` previously drifted (`backend/app/db/migrations/versions/001_initial.py`, `003_workspace_members_updated_at.py`).
- All workspace data access must be constrained by `workspace_id`; cross-workspace authorization has dedicated regression tests (`backend/app/tests/integration/test_authorization.py`).
- Extension quick-create/quick-action carry `workspace_id` in JSON rather than query parameters; this is a documented contract exception (`docs/API_SPEC.md`).
- The project explicitly forbids automated LinkedIn actions, inbox/DOM scraping and content-script automation (`docs/DECISIONS.md`, `docs/PRODUCT_OVERVIEW.md`).
- Frontend lint is not a reliable gate until its ESLint configuration is restored; tests and `tsc`/Vite build are the current verified gates (`frontend/package.json`).
- The integration database is SQLite; PostgreSQL-only column behavior (ARRAY, advanced indexes/operators) needs explicit fixture emulation or a PostgreSQL-specific test gate.
- Production schema changes require an Alembic upgrade before code reads new non-optional columns.
- Route-level frontend files are already large (notably `PeopleListPage.tsx`); new complex behavior should be extracted into domain components/hooks instead of expanding the page indefinitely.

## Unknowns

- Needs Architect Decision: durable job infrastructure/provider for background imports, notifications, reports and backups.
- Needs Architect Decision: production email provider and sender domain.
- Needs Architect Decision: object storage provider for attachments, reports and backups.
- Needs Architect Decision: billing provider/product catalog and enforcement policy.
- Needs Architect Decision: LLM provider, data-retention policy and per-workspace AI consent model.
- Needs Architect Decision: whether release identifiers update package versions only, create Git tags/releases, or both.
