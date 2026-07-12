# PRD: NetworkPilot CRM Versioned Expansion Program

## 1. Problem

NetworkPilot CRM now covers manual LinkedIn outreach tracking, CSV-based contact intake, filtering, and favourite profiles, but users still rely on manual repetition for bulk maintenance, reminders, collaboration, reporting, and integrations. Adding all requested capabilities without explicit release boundaries would create contract drift, unsafe migrations, inconsistent permissions, and an untestable product. The product therefore needs a sequential, independently releasable 45-capability program.

## 2. Users

- **Workspace owner:** owns the workspace, data, integrations, billing, members, permissions, backups, and destructive actions.
- **Workspace admin (introduced `v0.0.24`):** manages people, workflows, tags, fields, integrations, and members within owner-granted limits.
- **Workspace editor (introduced `v0.0.24`):** manages assigned CRM data and activities but not workspace security/billing.
- **Workspace viewer (introduced `v0.0.24`):** reads permitted CRM data and reports without mutation rights.
- **Personal user before collaboration releases:** retains the current owner/member behavior until invitations and RBAC ship.
- **Integration client:** uses scoped API credentials only after `v0.0.44`.

## 3. Goals

1. Deliver every capability in `docs/VERSION_ROADMAP.md` as an independently testable release in exact numeric order.
2. Preserve workspace isolation and the manual-only/no-scraping LinkedIn safety boundary across all 45 releases.
3. Require zero undocumented API, database, event, auth, config, or shared-type contract changes.
4. Keep each release backward-compatible unless its approved Contract Change Record defines a migration window.
5. Produce deployable migrations, automated coverage, manual QA evidence, and documentation for every release.

## 4. Non-Goals

- No automated LinkedIn connection requests, messages, browsing, inbox scraping, search-result scraping, DOM scraping, or content scripts.
- No feature may be pulled ahead of its assigned version because a later feature appears convenient.
- No production integration is enabled before provider credentials, consent, security, retention, failure behavior, and revocation are designed.
- No AI feature may silently send workspace data to a model provider.
- No billing enforcement is introduced before `v0.0.45`.
- No package manifest downgrade from `0.1.0` to `0.0.x`; `v0.0.N` is the product release/tag train.

## 5. V1 Scope

The expansion program scope is the exact 45-release registry in `docs/VERSION_ROADMAP.md`. Each row is mandatory, ordered, and maps one-to-one to `MAS-1` through `MAS-45`. A version is user-visible only after its complete ticket set passes the global release gates.

Behavioral constraints shared by all releases:

1. All persisted records are workspace-scoped unless explicitly global and security-reviewed.
2. All list/search/export operations apply authorization and filtering before pagination or file generation.
3. Destructive user actions require explicit confirmation and preserve a recovery/audit mechanism where the data model supports it.
4. Background work must be durable, idempotent, observable, retry-safe, and resumable after process restart.
5. Integrations must support connect, health/status, failure, retry, disconnect/revoke, and data-deletion behavior.
6. AI output is editable, labeled as generated, source-grounded, and never executes an outreach action.

## 6. Future Scope (V2+)

- LinkedIn-approved official APIs if a compliant product partnership becomes available.
- Native iOS/Android clients beyond the PWA release.
- Enterprise SSO/SCIM, data residency, and legal hold.
- Marketplace ecosystem beyond the signed webhooks/API released in `v0.0.30` and `v0.0.44`.
- Multi-region active-active infrastructure.

## 7. User Flows

### A. Versioned delivery

1. Architect selects the next unshipped `v0.0.N` → 2. contracts and tickets are frozen → 3. builders implement gated tickets → 4. automated and manual QA pass → 5. release is merged, deployed, documented, and tagged → 6. only then may `v0.0.N+1` begin implementation.

### B. Daily CRM operation

1. User opens Dashboard/People → 2. uses filters, saved views, queues, or command palette → 3. selects a person or bulk set → 4. records manual outreach state, notes, tasks, ownership, or reminders → 5. system persists workspace-scoped changes and audit events → 6. dashboards/reports reflect the change.

### C. Collaboration

1. Owner invites a member (`v0.0.23`) → 2. member accepts securely → 3. owner/admin assigns a role (`v0.0.24`) → 4. user receives assignments and mentions → 5. every mutation is authorized and audited.

### D. Integration

1. Authorized user starts provider connection → 2. system displays requested scopes and consent → 3. OAuth callback stores encrypted/rotatable credentials → 4. durable jobs synchronize or notify → 5. failures surface with retry/disconnect controls → 6. revocation removes access and schedules retained-data cleanup.

### E. AI assistance

1. User opts in and invokes an AI feature → 2. UI shows the exact data categories to be sent → 3. backend constructs an allowlisted prompt → 4. provider returns a draft/suggestion/summary → 5. user reviews and edits → 6. only explicit user action saves or copies output; no LinkedIn action is automated.

## 8. Roles & Permissions

Until `v0.0.24`, existing owner/member access remains unchanged. From `v0.0.24` onward:

| Action | Owner | Admin | Editor | Viewer |
|---|---:|---:|---:|---:|
| Read people/activities/tasks/reports | yes | yes | yes | yes |
| Create/update CRM records | yes | yes | yes | no |
| Bulk update/archive/restore | yes | yes | yes | no |
| Manage tags, fields, stages, goals | yes | yes | no | no |
| Invite/remove members | yes | yes, except owner | no | no |
| Change roles | yes | yes, below admin only | no | no |
| Configure integrations/notifications | yes | yes | no | no |
| View audit log | yes | yes | no | no |
| Manage API keys | yes | yes | no | no |
| Manage billing, ownership, workspace deletion | yes | no | no | no |

## 9. Data Model (conceptual)

Existing: users, workspaces, workspace members, people, activities, templates, import batches/settings. Expansion entities: bulk operations, saved views, merge records, import jobs/files, tag definitions/assignments, notifications/preferences/deliveries, pipeline stages, custom field definitions/values, structured notes, tasks, person ownership, attachments, relationship scores, analytics snapshots, goals, report jobs, invitations, comments/mentions, audit events, integration connections, OAuth tokens, webhook endpoints/deliveries, AI generations, backup jobs/artifacts, API keys, subscriptions/entitlements/usage events.

Every workspace-owned table includes `workspace_id`, UUID primary key, timestamps, foreign-key indexes, and explicit deletion/retention behavior. Sensitive tokens and API secrets are encrypted/hashed and never returned after creation.

## 10. APIs (conceptual)

- Bulk preview/commit/status APIs.
- Saved-view CRUD and resolve APIs.
- Duplicate candidate and merge preview/commit APIs.
- Durable job CRUD/status/retry/artifact APIs for import, reports, backup, notification, integrations, and AI.
- Workspace configuration CRUD for tags, pipeline stages, custom fields, goals, notification preferences, webhooks, API keys, and billing.
- Collaboration APIs for invitations, membership, permissions, ownership, tasks, comments, mentions, and audit events.
- Search/analytics/reporting APIs.
- OAuth connect/callback/status/disconnect APIs per provider.
- Extension session-handoff and expanded profile/task APIs.

Exact route and payload contracts are owned by the architecture plan and per-release Contract Change Records.

## 11. Frontend Requirements

- Existing Dashboard, People, Person Detail, Templates, Settings and extension screens are extended through extracted domain components rather than continued monolithic page growth.
- New route groups: Tasks, Notifications, Imports, Reports, Trash, Team, Audit, Integrations, Billing and workspace configuration.
- Every screen includes loading, empty, error, success, permission-denied, mobile and keyboard states as applicable.
- Bulk/destructive actions show selected counts, impact preview, confirmation, per-record results, retry, and recovery guidance.
- Integration/AI/payment screens show consent, scope, data-use and failure status plainly.

## 12. Backend Requirements

- FastAPI service-layer conventions, Pydantic validation, standard AppError envelope and workspace authorization remain mandatory.
- A durable database/queue job system must be selected before `v0.0.4`; in-process FastAPI background tasks are prohibited for durable work.
- External calls require timeouts, bounded retries, idempotency, provider rate-limit handling and observable failure states.
- Storage-backed capabilities require private object storage, workspace-scoped keys, size/type validation, short-lived downloads, malware strategy where attachments are introduced, and retention deletion.
- Security-sensitive releases require premium review: permissions, invitations, OAuth, webhooks, extension auth, AI data flow, backup/restore, API keys and billing.

## 13. Micro-Architecture Systems

The version registry maps directly: `MAS-1 Bulk Actions` = `v0.0.1`, continuing sequentially through `MAS-45 Billing and Plans` = `v0.0.45`. Each MAS owns only its release capability and frozen contracts, depends on all earlier contract prerequisites, and must be split into no more than six self-contained tickets. The canonical names and outcomes are in `docs/VERSION_ROADMAP.md`.

Cross-cutting dependency groups:

- MAS-1–8: personal CRM efficiency foundation.
- MAS-9–17: configurable workflow and data model.
- MAS-18–22: analytics/reporting built on stable workflow data.
- MAS-23–27: collaboration and authorization foundation.
- MAS-28–34: consented integrations and extension identity.
- MAS-35–39: AI assistance and import intelligence.
- MAS-40–45: platform experience, portability, developer access and monetization.

## 14. Success Metrics

1. Each release has 100% passing global release gates and zero Critical/High code-review findings at merge.
2. Workspace-isolation and authorization regression suites remain green through all releases.
3. Core People list and mutation endpoints maintain p95 under 500 ms for 10,000-person workspaces, excluding explicitly asynchronous jobs.
4. Durable jobs reach at least 99% terminal completion without operator intervention, excluding invalid user input/provider outages.
5. Manual-only LinkedIn boundary has zero violations.

## 15. Risks

- **Program size:** 45 releases invite drift. Mitigation: immutable registry, one release at a time, contracts and per-version tags.
- **Schema growth:** custom fields, analytics and integrations may degrade queries. Mitigation: explicit indexes, query plans, migration rehearsal and retention policies.
- **Authorization expansion:** collaboration increases cross-workspace/data-leak risk. Mitigation: centralized permissions and negative integration tests.
- **External provider instability:** OAuth/email/calendar/Slack failures. Mitigation: durable jobs, idempotency, retries, disconnect and user-visible status.
- **AI privacy/cost:** model providers receive user data and generate unreliable content. Mitigation: opt-in, minimization, retention controls, edit-only output and usage metering.
- **Billing lockout:** incorrect entitlements could block paid users. Mitigation: append-only usage events, webhook verification, grace states and owner-visible diagnostics.

## 16. Open Questions

- Needs Product Decision: select durable job/queue provider before architecture for `v0.0.4`.
- Needs Product Decision: select email provider/domain before `v0.0.6` and `v0.0.23`.
- Needs Product Decision: select private object storage before `v0.0.16`, `v0.0.22`, and `v0.0.43`.
- Needs Product Decision: define member seat/invitation policy before `v0.0.23`.
- Needs Product Decision: select OAuth application ownership and consent-screen accounts before `v0.0.28`–`v0.0.32`.
- Needs Product Decision: select LLM provider, data retention and AI usage budget before `v0.0.35`.
- Needs Product Decision: choose billing provider, currency, plans, trial and grace policy before `v0.0.45`.
