# NetworkPilot CRM Version Roadmap

Status: Architect-approved program registry  
Canonical release identifier: `v0.0.N`  
Rule: one numbered product capability per release, in the exact order below.

Package manifests currently use `0.1.0`. The roadmap identifier is a product release/Git tag and does not rewrite package versions. A release tag is created only after its ticket set is merged, migrations are deployable, automated checks pass, and manual QA evidence is recorded.

| Version | Capability | Release outcome |
|---|---|---|
| `v0.0.1` | Bulk actions | Select people and bulk-update favourite, tags, priority, stage, archive state, or next action. |
| `v0.0.2` | Saved filters and smart lists | Persist workspace-scoped People views and reapply them safely. |
| `v0.0.3` | Duplicate detection and merging | Detect likely duplicates and merge profile/activity data with an audit trail. |
| `v0.0.4` | Import job centre | Durable background imports, progress, retry, history, and error reports. |
| `v0.0.5` | Custom tags | Workspace-managed coloured tags, bulk assignment, filtering, and widgets. |
| `v0.0.6` | Better reminders | In-app/email reminders, daily digest, overdue alerts, and quiet hours. |
| `v0.0.7` | Quick favourite controls | Toggle favourites from People and the extension without opening detail. |
| `v0.0.8` | Restore archived/deleted people | Trash/archive views with restore and undo. |
| `v0.0.9` | Custom pipeline stages | Workspace-defined stages, ordering, and transition configuration. |
| `v0.0.10` | Custom fields | Workspace-defined text, number, date, dropdown, and checkbox fields. |
| `v0.0.11` | Saved notes and interaction summaries | Structured notes, outcomes, summaries, and next steps. |
| `v0.0.12` | Tasks | Multiple assignable tasks per person with status, due dates, and reminders. |
| `v0.0.13` | Contact ownership | Assign people to workspace members and filter by owner. |
| `v0.0.14` | Bulk CSV editing | Export filtered data and re-import updates without creating duplicates. |
| `v0.0.15` | Advanced search | Search across profile, favourite, activity, tag, phone, website, and date data. |
| `v0.0.16` | Timeline improvements | Edit/delete/pin/filter activities and attach files. |
| `v0.0.17` | Relationship strength | Manual warmth plus calculated freshness/engagement indicators. |
| `v0.0.18` | Outreach funnel | Stage conversion metrics from saved through replied. |
| `v0.0.19` | Follow-up performance | Response metrics by template, stage, company, position, and time. |
| `v0.0.20` | Dashboard widgets | Configurable favourite, accepted, stale, overdue, and import widgets. |
| `v0.0.21` | Goals | Weekly outreach targets and progress. |
| `v0.0.22` | Exportable reports | Filtered CSV/PDF analytics reports. |
| `v0.0.23` | Workspace invitations | Invite members by email and manage membership lifecycle. |
| `v0.0.24` | Role-based permissions | Owner/admin/editor/viewer authorization enforced server-side. |
| `v0.0.25` | Comments and mentions | Profile discussions, mentions, and notifications. |
| `v0.0.26` | Audit log | Immutable workspace event history for sensitive changes. |
| `v0.0.27` | Assignments and team queues | My People/My Tasks queues and team assignment workflows. |
| `v0.0.28` | Google Calendar OAuth | Recurring reminders and direct follow-up event creation. |
| `v0.0.29` | Gmail integration | Permissioned email association and reply detection. |
| `v0.0.30` | Webhook/API integrations | Signed event delivery and external automation API. |
| `v0.0.31` | Slack notifications | Daily digests and overdue alerts in Slack. |
| `v0.0.32` | Google Contacts sync | Permissioned contact import/update without LinkedIn scraping. |
| `v0.0.33` | Extension authentication | Secure session handoff replacing pasted access tokens. |
| `v0.0.34` | Extension enhancements | Favourite, notes, activity, due actions, and task creation in popup. |
| `v0.0.35` | Personalized message drafts | Consent-gated editable AI drafts grounded in profile data/templates. |
| `v0.0.36` | Follow-up suggestions | Explainable recommended next action and timing. |
| `v0.0.37` | Note summarization | Consent-gated summaries of activity and relationship history. |
| `v0.0.38` | Natural-language filtering | Translate user queries into allowlisted People filters. |
| `v0.0.39` | CSV column mapping assistant | Suggest and confirm mappings for unfamiliar CSV headers. |
| `v0.0.40` | Mobile/PWA experience | Installable responsive app with scoped offline behavior. |
| `v0.0.41` | Command palette | Keyboard-driven search and common actions. |
| `v0.0.42` | Notification preferences | Per-workspace, per-channel, quiet-hour, and digest controls. |
| `v0.0.43` | Data backup and portability | Full workspace export, scheduled backups, and tested restore. |
| `v0.0.44` | API keys | Scoped, hashed, rotatable integration credentials with audit history. |
| `v0.0.45` | Billing and plans | Subscription plans, entitlements, usage metering, and enforcement. |

## Global release gates

Every version must satisfy all of the following before its tag is created:

1. PRD behavior and acceptance metrics for that capability are met.
2. Any API, database, event, auth, or shared-type change has a Contract Change Record.
3. Upgrade and rollback migration paths are documented and tested when schema changes exist.
4. Workspace isolation and role authorization have integration coverage.
5. Frontend loading, empty, error, success, keyboard, and mobile states are implemented.
6. Backend, frontend, extension (when touched), type/build, and relevant manual QA gates pass.
7. `docs/API_SPEC.md`, `docs/DATABASE_SCHEMA.md`, and user documentation are updated when affected.
8. No automated LinkedIn action, DOM scraping, inbox scraping, or content-script automation is introduced.

