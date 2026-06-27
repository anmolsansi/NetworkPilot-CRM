# NetworkPilot CRM

A personal CRM for tracking LinkedIn outreach follow-ups. Browse LinkedIn, save profiles, track stages, and never lose track of who needs follow-up.

## Project Structure

```
NetworkPilot-CRM/
├── frontend/       # React + Vite + TypeScript web app
├── backend/        # FastAPI + SQLAlchemy + Alembic
├── extension/      # React MV3 Chrome extension
└── docs/           # Planning and architecture docs
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React, Vite, TypeScript, Tailwind CSS, Zustand |
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic |
| Database | Supabase Postgres |
| Auth | Supabase Auth (JWT) |
| Extension | React MV3 Chrome Extension |

## Local Setup Order

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env      # Fill in Supabase credentials
alembic upgrade head
uvicorn app.main:app --reload
```

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env      # Fill in Supabase credentials
npm run dev
```

### 3. Extension

```bash
cd extension
npm install
cp .env.example .env      # Set API base URL
npm run build
# Load unpacked from extension/dist in Chrome
```

## Development Commands

```bash
# Install all dependencies
npm run install:all

# Run frontend dev server
npm run dev:frontend

# Run extension dev server
npm run dev:extension

# Run backend
npm run test:backend

# Run frontend tests
npm run test:frontend

# Lint frontend
npm run lint:frontend

# Format code
npm run format

# Check formatting
npm run format:check
```

## Documentation

### Planning
- [Product Overview](docs/PRODUCT_OVERVIEW.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Database Schema](docs/DATABASE_SCHEMA.md)
- [API Spec](docs/API_SPEC.md)
- [Frontend Plan](docs/FRONTEND_PLAN.md)
- [Backend Plan](docs/BACKEND_PLAN.md)
- [Decisions](docs/DECISIONS.md)
- [Tasks](docs/TASKS.md)

### Setup & Deployment
- [Supabase Setup](docs/SUPABASE_SETUP.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Extension Installation](docs/EXTENSION_INSTALL.md)
- [Extension QA Checklist](docs/EXTENSION_QA.md)

### User Guide
- [V1 User Guide](docs/V1_USER_GUIDE.md)
- [QA Results](docs/QA_RESULTS.md)
- [Bug Tracker](docs/BUGS_FOUND.md)

## Implementation Order

1. **Database** — Set up Supabase, create tables, run migrations
2. **Backend** — FastAPI app, auth, people/activities API, extension endpoints
3. **Frontend** — React app, auth flow, dashboard, people, templates, settings
4. **Extension** — MV3 extension, quick save/update, template copy
5. **Testing** — Unit tests, integration tests, smoke tests
6. **Deployment** — Render (backend), Vercel (frontend), extension package

## V1 Status

**V1 Complete** - All 62 tickets implemented.

### What's Working
- ✅ User authentication (Supabase)
- ✅ Workspace management
- ✅ People tracking with stages
- ✅ Activity timeline
- ✅ Stage transition rules
- ✅ Dashboard with due follow-ups
- ✅ Message templates with copy
- ✅ Chrome extension for quick actions
- ✅ Calendar reminder link
- ✅ Unit and integration tests

### What's NOT in V1
- ❌ Automated LinkedIn messaging
- ❌ Automated connection requests
- ❌ LinkedIn inbox scraping
- ❌ LinkedIn DOM scraping
- ❌ Gmail integration
- ❌ Google Calendar OAuth
- ❌ AI-generated messages
- ❌ CSV import/export
- ❌ Team features
- ❌ Billing

## V1 Scope

Manual LinkedIn outreach tracking only. No automation of connection requests, messages, or inbox scraping. The Chrome extension is manual-click only. The backend is the source of truth for stage transitions.
