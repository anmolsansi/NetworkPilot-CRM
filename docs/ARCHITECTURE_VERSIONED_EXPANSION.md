# Architecture Plan: NetworkPilot CRM Versioned Expansion Program

## 1. Stack Decisions

| Layer | Choice | Reason |
|---|---|---|
| Frontend | Existing React 18 + TypeScript + Vite + Tailwind | Preserve deployed stack and current route/component conventions. |
| Frontend state | Zustand for global auth/workspace; local feature hooks for transient UI | Existing convention; avoids adding a dependency before a dedicated data-layer ticket. |
| Backend | Existing FastAPI + Pydantic 2 + SQLAlchemy 2 async | Preserve deployed API and service-layer conventions. |
| Database | Existing Supabase PostgreSQL + Alembic | Workspace isolation, relational integrity and migration history already established. |
| Auth | Existing Supabase JWT | No auth change before `v0.0.33`; roles remain owner/member until `v0.0.24`. |
| Jobs | BLOCKED before `v0.0.4` | Needs Product Decision: durable provider. FastAPI in-process background tasks are prohibited. |
| Storage | BLOCKED before first attachment/report/backup artifact | Needs Product Decision: private object storage provider. |
| Email | BLOCKED before `v0.0.6`/`v0.0.23` | Needs Product Decision: provider/domain. |
| LLM | BLOCKED before `v0.0.35` | Needs Product Decision: provider, retention, consent and budget. |
| Billing | BLOCKED before `v0.0.45` | Needs Product Decision: provider, plans, currency, trial and grace rules. |

Product releases use tags `v0.0.N`; existing npm/Python package versions remain `0.1.0` until a separate architect-approved release-management contract changes them.

## 2. Frontend Architecture

- Routes remain under `frontend/src/app/routes.tsx` with `RequireAuth` and `AppLayout`.
- New complex capabilities use `frontend/src/features/<feature>/components`, `hooks`, `types.ts`, and (where the shared client permits) `api.ts`.
- Existing API auth/base/error normalization stays in `frontend/src/api/httpClient.ts`; feature APIs must delegate to it.
- Shared visual primitives remain in `frontend/src/components/common`.
- Route pages own orchestration only. `PeopleListPage.tsx` must shrink over time; new bulk UI begins in a feature component.
- No frontend feature directly trusts workspace/user IDs for authorization; the API revalidates every request.
- Mandatory states: loading, empty, error/retry, success confirmation, permission denied, keyboard and 375px layout.

## 3. Backend Architecture

- Existing layering remains route → service → SQLAlchemy ORM → PostgreSQL.
- Pydantic schemas in `backend/app/schemas` own boundary validation; domain errors use `backend/app/core/errors.py`.
- Every workspace-scoped service query includes `workspace_id` and active/deleted constraints appropriate to the resource.
- Cross-capability communication occurs through service methods and frozen API/database/event contracts, never through frontend assumptions.
- Durable work records status in PostgreSQL and is processed by the future selected job system; no durable feature uses process-local tasks.

## 4. Database Architecture

Existing tables remain: `app_users`, `workspaces`, `workspace_members`, `people`, `activities`, `message_templates`, `user_settings`, `import_batches`.

Planned tables by release are architect-frozen only when that release architecture is approved. The intended table ownership is:

| Release/MAS | Tables or schema changes |
|---|---|
| 1 Bulk actions | No new table; atomic updates to `people`, with activities created where the action represents a timeline event. |
| 2 Saved views | `saved_people_views` (workspace/user/name/filter JSON/sort fields). |
| 3 Merge | `person_merges` plus source→target references; existing activities reassigned transactionally. |
| 4 Import jobs | replace/extend `import_batches` through safe additive migrations after job/storage selection. |
| 5 Tags | `tag_definitions`, `person_tags`; migrate existing `people.tags` compatibly. |
| 6 Notifications | `notifications`, `notification_deliveries`, `notification_preferences`. |
| 7 Quick favourite | no schema change. |
| 8 Restore | no schema change; restoration metadata may be added through CCR if required. |
| 9 Pipeline | `pipeline_stages`; `people.stage` compatibility migration. |
| 10 Custom fields | `custom_field_definitions`, `person_custom_field_values`. |
| 11 Structured notes | `person_notes`. |
| 12 Tasks | `tasks`, indexed by workspace/assignee/status/due date. |
| 13 Ownership | nullable `people.owner_user_id` FK after invitations foundation compatibility review. |
| 14 Bulk CSV editing | import job update mode fields; no duplicate schema. |
| 15 Search | PostgreSQL search indexes/materialized vectors selected after query evaluation. |
| 16 Timeline | activity soft-delete/edit/pin fields plus `activity_attachments`. |
| 17 Relationship strength | person manual warmth + calculated score snapshot fields/history. |
| 18–20 Analytics/widgets | aggregate queries first; snapshots only after measured need. |
| 21 Goals | `workspace_goals`, `goal_progress_snapshots`. |
| 22 Reports | `report_jobs`, private report artifacts. |
| 23 Invitations | `workspace_invitations` with hashed token, expiry, inviter and status. |
| 24 RBAC | role constraint migration on `workspace_members`; centralized permission map. |
| 25 Comments | `person_comments`, `comment_mentions`. |
| 26 Audit | append-only `audit_events`. |
| 27 Assignments | ownership/tasks reused; queue views are queries. |
| 28–32 Integrations | `integration_connections`, provider-specific cursors, deliveries/sync jobs. |
| 30 Webhooks | `webhook_endpoints`, `webhook_deliveries`, hashed signing secret metadata. |
| 33 Extension auth | short-lived handoff records if required by approved flow. |
| 34 Extension enhancements | reuse earlier tables. |
| 35–39 AI/mapping | `ai_generations` and mapping presets only after consent/retention contracts. |
| 40 PWA | no business table; offline cache excludes sensitive bulk data by default. |
| 41 Command palette | no schema unless saved commands are later approved. |
| 42 Preferences | extend/normalize `notification_preferences`. |
| 43 Backup | `backup_jobs`, private artifact metadata and restore rehearsals. |
| 44 API keys | `api_keys` with hash, prefix, scopes, expiry, last-used and revocation. |
| 45 Billing | `subscriptions`, `entitlements`, `usage_events`, webhook events. |

All exact future columns, constraints, indexes and retention behavior must be frozen in that release's CCR before tickets exist. No builder may infer them from this ownership map.

## 5. API Architecture

- Base remains `/api/v1`.
- Current success shapes remain backward-compatible (direct objects/lists and People pagination) unless a new endpoint explicitly adopts a release-local shape.
- Errors remain `{error:{code,message,details}}`; the skill's different standard envelope is not retrofitted without a breaking-version plan.
- New list endpoints are paginated with current repo naming `page` and `limit` (1–100) for compatibility.
- Unknown Pydantic request-body fields must be rejected on new contracts through `extra="forbid"`.
- Full `v0.0.1` endpoint contract appears in CCR-001 and is copied into its backend/frontend tickets.
- Later endpoints are not frozen until their release architecture gate; conceptual capabilities are listed in the PRD and may not be implemented from names alone.

## 6. Auth & Permissions

- Supabase bearer JWT → `get_current_auth` → `get_current_user` → `require_workspace_access` remains the flow.
- Through `v0.0.23`, owner/member retain current workspace access behavior.
- `v0.0.24` introduces the Owner/Admin/Editor/Viewer permission table in the PRD and must centralize checks before later team/integration features proceed.
- Unauthorized cross-workspace IDs return a non-enumerating not-found/validation outcome defined by each contract.
- Security-premium review is mandatory for releases 23–25, 28–33, 35–39, 43–45.

## 7. Background Jobs

Blocked until the `v0.0.4` provider decision. Required job contract fields across later releases: UUID job ID, workspace ID, actor ID, type, idempotency key, status (`pending|processing|completed|failed|cancelled` as approved), attempts/max attempts, progress totals, safe error code/message, timestamps. Jobs must be idempotent and terminally observable.

## 8. File Storage

Cloudflare R2 is the selected provider. Attachment objects use a private bucket, generated workspace/activity-scoped keys, extension+MIME+signature+size validation, five-minute signed downloads, and authorized deletion. R2 credentials remain backend-only. A malware-scanning service is still required before broadening the attachment allowlist beyond the currently validated document, text, and image formats.

## 9. Integrations

Google Calendar, Gmail, Slack and Google Contacts require OAuth with minimum scopes, encrypted refresh tokens, provider status, retry cursors, disconnect/revoke and retained-data deletion. Webhooks require hashed signing secrets and signature verification. No integration contract is buildable until its Product Decision and security CCR are approved.

## 10. Observability

- Reuse structured backend logging/request IDs and frontend logger utilities.
- Log job/integration lifecycle with masked IDs, never tokens, secrets, raw PII, note content or AI prompts.
- `/api/v1/health` remains the liveness endpoint; future readiness/provider health endpoints require explicit contracts.
- Release done reports record test counts, migration up/down results and manual QA evidence.

## 11. Deployment Assumptions

- Frontend: Vercel; backend: Render; database/auth: Supabase.
- Additive database migrations deploy before code that requires new fields.
- Each release merges independently and is tagged only after deployment/QA gates.
- CI behavior is not assumed; current local gates are backend pytest, frontend Vitest/build, extension test/build when touched, Alembic head/migration checks and manual QA.

## 12. System Boundaries & Contracts

### CONTRACT MAS-1 UI → MAS-1 API: bulk People mutation

- `POST /api/v1/people/bulk-actions`; auth required; workspace membership required.
- Request and response are frozen in `docs/contract_changes/CCR-001-bulk-people-actions.md`.
- Max 100 unique person IDs. Atomic: any inaccessible/missing ID or invalid action aborts the whole mutation.
- Owner: MAS-1 backend. Frontend consumes without changing fields.

### CONTRACT all frontend features → shared HTTP client

- All JSON/blob calls use `frontend/src/api/httpClient.ts` for token/base/error behavior.
- Feature code never reads Supabase tokens directly.
- Owner: platform/auth context; changes require CCR.

### CONTRACT all workspace MAS → workspace access

- Every request supplies contract-located `workspace_id`; backend verifies active membership before resource access.
- Every SQL query additionally scopes records by workspace.
- Owner: auth/workspace context; changes require security CCR.

### CONTRACT durable MAS → future job platform

- BLOCKED. No implementation/ticket may invent queue names, payloads, retries or provider until `v0.0.4` decision and CCR.

## 13. Parallelization Map

- Releases are implemented sequentially in version order.
- Within one release, tickets may be parallel only after contracts freeze and dependencies permit it.
- `v0.0.1`: backend contract implementation can precede or run alongside mocked frontend UI; integration wiring follows backend and frontend unit/API tests.
- Versions 2–3 depend on stable People bulk/list contracts. Version 4 blocks durable-job consumers in 6, 22, 28–32, 35–39, 43 and 45.
- Versions 23–24 block team permissions, assignments and team-scoped integrations.

## 14. Risk Register

- Bulk atomicity and workspace enumeration (`v0.0.1`) — premium review required.
- Live-data migrations and custom-field/tag normalization — premium review required.
- Durable jobs/concurrency/import retries — premium review required.
- Invitations/RBAC/OAuth/extension auth/API keys/billing — security-premium review required.
- Webhook verification and external retries — security-premium review required.
- AI prompt privacy, injection and usage metering — security-premium review required.
- Backup restore correctness — destructive-operation rehearsal and premium review required.
