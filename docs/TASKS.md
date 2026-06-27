# Tasks

## Implementation Status

See `DEVELOPMENT_BACKLOG.md` for the full ticket list with dependencies.

## Phase Summary

| Phase | Name | Tickets | Status |
|-------|------|---------|--------|
| 1 | Project Setup | 1-3 | In Progress |
| 2 | Database Setup | 4-8 | Pending |
| 3 | Backend Foundation | 9-11 | Pending |
| 4 | Auth & Authorization | 12-15 | Pending |
| 5 | Core Backend Domain | 16-24 | Pending |
| 6 | Dashboard, Templates, Calendar | 25-29 | Pending |
| 7 | Extension Backend Endpoints | 30-32 | Pending |
| 8 | Web Frontend Foundation | 33-37 | Pending |
| 9 | Web Frontend Features | 38-42 | Pending |
| 10 | Extension Foundation | 43-46 | Pending |
| 11 | Extension Features | 47-50 | Pending |
| 12 | Testing | 51-54 | Pending |
| 13 | Deployment | 55-59 | Pending |
| 14 | V1 Validation | 60-62 | Pending |

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
