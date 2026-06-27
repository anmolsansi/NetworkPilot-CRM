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

## Future Considerations (V2+)

- Gmail notification parsing
- Google Calendar OAuth for true recurring events
- AI-generated personalized messages
- CSV import/export
- Team invitation and collaboration
- Chrome Web Store publishing
- Mobile app
