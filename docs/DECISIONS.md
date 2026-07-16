# Decisions

## V1 Architecture Decisions

### 1. Supabase for Auth + Database
**Decision**: Use Supabase for both Postgres hosting and Auth.
**Why**: Reduces backend auth complexity. Supabase provides JWT verification, user management, and hosted Postgres.
**Trade-off**: Vendor lock-in, but Supabase is open-source and can be self-hosted.

### 2. Backend as Source of Truth
**Decision**: All stage transitions go through the backend API.
**Why**: Prevents inconsistent state between web app and extension. Extension calls API, never mutates directly.
**Trade-off**: Slightly more network calls, but ensures data integrity.

### 3. Manual Only
**Decision**: No automation of LinkedIn actions (connection requests, messages, DOM scraping).
**Why**: Avoids LinkedIn TOS violations, account bans, and complexity. V1 focuses on tracking, not automation.
**Trade-off**: Less "magic", but safer and simpler.

### 4. Popup-Only Extension
**Decision**: Chrome extension uses popup UI only, no content scripts.
**Why**: Content scripts inject into LinkedIn pages, which is risky for TOS and stability. Popup reads URL from tab API.
**Trade-off**: User must click extension icon, but no LinkedIn interference.

### 5. Soft Deletes
**Decision**: Never hard delete people or templates. Use `deleted_at` timestamp.
**Why**: Preserves data integrity, allows recovery, prevents cascade issues.
**Trade-off**: Slightly more complex queries (filter by deleted_at IS NULL).

### 6. Workspace Isolation
**Decision**: All data scoped to workspace via `workspace_id` foreign key.
**Why**: Supports future multi-workspace feature. Clear data boundaries.
**Trade-off**: Extra column on every table, but necessary for isolation.

### 7. URL Normalization
**Decision**: Normalize LinkedIn profile URLs to prevent duplicates.
**Why**: Same profile can be accessed via different URLs (tracking params, www vs non-www).
**Trade-off**: Need to maintain normalization logic, but prevents duplicate records.

### 8. Static Templates
**Decision**: V1 uses static message templates with copy-to-clipboard.
**Why**: Simple, no AI costs, user controls content. Extension renders variables and copies.
**Trade-off**: No AI personalization, but faster and free.

### 9. Calendar Links (Not OAuth)
**Decision**: Generate Google Calendar URLs instead of OAuth integration.
**Why**: No token management, no Google API complexity. URL creates a daily reminder intent.
**Trade-off**: Not a true recurring event, but sufficient for V1.

### 10. Zustand for Frontend State
**Decision**: Use Zustand instead of Redux or Context.
**Why**: Minimal boilerplate, good TypeScript support, simple API.
**Trade-off**: Smaller ecosystem than Redux, but sufficient for this app size.

### 11. Temporary Extension Auth Setup
**Decision**: For internal MVP QA, the extension may accept manually pasted API URL, Supabase access token, and workspace ID.
**Why**: Avoids building full extension OAuth/session handoff before core tracking flow is stable.
**Follow-up**: Replace or improve before external users; document token storage risk.

## Cloudflare R2 for private attachments

**Decision**: Store activity attachments in a private Cloudflare R2 bucket through its S3-compatible API.

**Why**: R2 provides durable object storage, private workspace-scoped keys, and short-lived presigned downloads without relying on ephemeral application disks.

**Operational constraints**: Keep R2 credentials backend-only, limit uploads to validated file types and 10 MB, issue five-minute download URLs only after workspace authorization, and delete the object before removing its database record.

**Follow-up**: Add a malware-scanning/quarantine service before expanding the file-type allowlist.

### 12. Canonical Workspace ID Transport
**Decision**: Workspace-scoped API endpoints must consistently pass `workspace_id` in the same location expected by backend authorization.
**Why**: Prevents extension/web clients from bypassing or breaking `require_workspace_access`.
**Follow-up**: Update API spec and tests to enforce this.

### 13. QA Evidence Standard
**Decision**: QA sign-off docs must include date, tester, environment, backend commit/version, frontend build, and extension build.
**Why**: Prevents stale or aspirational QA docs from being treated as release evidence.

### 14. API Contract Documentation Is Binding
**Decision**: `API_SPEC.md` must be updated in the same patch whenever frontend, extension, or backend route contracts change.
**Why**: The extension `workspace_id` mismatch happened because implementation and contract documentation drifted.
**Follow-up**: Add API spec review to each backend/frontend/extension contract change.

### 15. Durable CSV Imports Use Database-Backed Jobs
**Decision**: CSV uploads are stored as durable jobs and processed by a separately deployed worker in 40-row checkpoints.
**Why**: Progress, retries, and error reports must survive browser and API process restarts.

### 16. Configuration References Use Workspace-Scoped UUIDs
**Decision**: Tags, pipeline stages, and custom-field values use stable UUID references that are validated against the active workspace.
**Why**: Names are editable and cannot safely serve as storage keys or tenant boundaries.

### 17. Empty Pipeline Transition Lists Mean Unrestricted
**Decision**: A custom stage with no `allowed_next_stage_ids` permits any next stage; a non-empty list is enforced by single and bulk updates.
**Why**: Existing workspaces remain compatible while teams can opt into controlled transitions.

### 18. Reminder Delivery Is In-App First
**Decision**: Due follow-ups create durable in-app notifications; email is an optional delivery channel governed by workspace preferences and quiet hours.
**Why**: A transient email-provider failure must not erase the underlying reminder.

### 19. Version Completion Requires Four-Dimension Acceptance Evidence
**Decision**: A version can be marked complete only after positive, negative, tenant-isolation,
and populated-data API evidence passes together with its user-facing workflow evidence on the
same integrated commit.
**Why**: Route existence and empty-response smoke tests did not detect authorization gaps,
frontend/backend contract drift, or populated-data crashes in v0.0.11-v0.0.23.
**Follow-up**: Expected failures identify unmerged prerequisites but never count as release
passes. Record the commit, environment, commands, and results in the release completion report.

## Future Considerations (V2+)

- Gmail notification parsing
- Google Calendar OAuth for true recurring events
- AI-generated personalized messages
- CSV import/export
- Team invitation and collaboration
- Chrome Web Store publishing
- Mobile app
