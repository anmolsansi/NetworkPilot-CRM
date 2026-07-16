# Tasks

## Implementation Status

See `DEVELOPMENT_BACKLOG.md` for the full ticket list with dependencies.

## Phase Summary

| Phase | Name | Tickets | Status |
|-------|------|---------|--------|
| 1 | Project Setup | 1-3 | Completed |
| 2 | Database Setup | 4-8 | Completed |
| 3 | Backend Foundation | 9-11 | Completed |
| 4 | Auth & Authorization | 12-15 | Completed |
| 5 | Core Backend Domain | 16-24 | Completed |
| 6 | Dashboard, Templates, Calendar | 25-29 | Completed |
| 7 | Extension Backend Endpoints | 30-32 | Completed |
| 8 | Web Frontend Foundation | 33-37 | Completed |
| 9 | Web Frontend Features | 38-42 | Completed |
| 10 | Extension Foundation | 43-46 | Completed |
| 11 | Extension Features | 47-50 | Completed |
| 12 | Testing | 51-54 | In Progress (Adding cross-workspace auth tests) |
| 13 | Deployment | 55-59 | Completed |
| 14 | V1 Validation | 60-62 | Incomplete (Awaiting valid QA evidence) |

## Versioned Expansion Remediation

| Version | Feature | Code status |
|---|---|---|
| v0.0.1 | Bulk actions | Complete |
| v0.0.2 | Saved filters and smart lists | Complete |
| v0.0.3 | Duplicate detection and merging | Complete |
| v0.0.4 | Import job centre | Complete |
| v0.0.5 | Custom tags | Complete |
| v0.0.6 | Better reminders | Complete |
| v0.0.7 | Quick favourite controls | Complete |
| v0.0.8 | Restore archived/deleted people | Complete |
| v0.0.9 | Custom pipeline stages | Complete |
| v0.0.10 | Custom fields | Complete |
| v0.0.11 | Saved notes and interaction summaries | Pending PR #63 and combined acceptance run |
| v0.0.12 | Tasks | Pending PR #64 and combined acceptance run |
| v0.0.13 | Contact ownership | Pending PR #65 and combined acceptance run |
| v0.0.14 | Bulk CSV editing | Pending PR #66 and browser acceptance evidence |
| v0.0.15 | Advanced search | Pending PR #67 and frontend acceptance evidence |
| v0.0.16 | Timeline improvements | Pending PRs #68-#69 and combined acceptance run |
| v0.0.17 | Relationship strength | Pending PR #70 and combined acceptance run |
| v0.0.18 | Outreach funnel | Pending PRs #61 and #71; tenant test currently expected-failing |
| v0.0.19 | Follow-up performance | Pending PRs #61 and #72; tenant test currently expected-failing |
| v0.0.20 | Dashboard widgets | Pending PR #73 and combined acceptance run |
| v0.0.21 | Goals | Pending PRs #61 and #74; tenant test currently expected-failing |
| v0.0.22 | Exportable reports | Pending PRs #61 and #75; tenant test currently expected-failing |
| v0.0.23 | Workspace invitations | Pending PRs #62 and #76; tenant test currently expected-failing |

Detailed acceptance evidence and merge prerequisites are recorded in
`releases/v0.0.11-v0.0.23-COMPLETION.md`. Release tags remain pending until the
individual remediation PRs are merged, migrations are applied in staging, all
expected failures become passes, and authenticated browser QA is recorded.

*Note: The broad V1 implementation is marked as incomplete until the extension authentication, workspace contract, cross-workspace tests, and verifiable QA evidence are fully corrected and recorded.*

## Quick Reference

### After Phase 1-2 (Database Ready)
- Backend can connect to Postgres
- All tables created via migrations
- Models match schema

### After Phase 3-4 (Auth Working)
- JWT verification works
- User bootstrap works
- Workspace access checks work

### After Phase 5-7 (API Complete)
- People CRUD works
- Activities and transitions work
- Dashboard queries work
- Extension endpoints work

### After Phase 8-9 (Frontend Complete)
- Login/logout works
- Dashboard shows due follow-ups
- People list and detail work
- Templates and settings work

### After Phase 10-11 (Extension Complete)
- Extension popup works
- Quick save/update works
- Template copy works

### After Phase 12-14 (V1 Complete)
- All tests pass
- Deployed to Render (backend) and Vercel (frontend)
- Extension loadable in Chrome
- Full manual QA passed
