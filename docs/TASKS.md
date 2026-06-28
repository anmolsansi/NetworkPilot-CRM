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
