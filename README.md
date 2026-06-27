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

- [Product Overview](docs/PRODUCT_OVERVIEW.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Database Schema](docs/DATABASE_SCHEMA.md)
- [API Spec](docs/API_SPEC.md)
- [Frontend Plan](docs/FRONTEND_PLAN.md)
- [Backend Plan](docs/BACKEND_PLAN.md)
- [Decisions](docs/DECISIONS.md)
- [Tasks](docs/TASKS.md)

## Implementation Order

1. **Database** — Set up Supabase, create tables, run migrations
2. **Backend** — FastAPI app, auth, people/activities API, extension endpoints
3. **Frontend** — React app, auth flow, dashboard, people, templates, settings
4. **Extension** — MV3 extension, quick save/update, template copy
5. **Testing** — Unit tests, integration tests, smoke tests
6. **Deployment** — Render (backend), Vercel (frontend), extension package

## V1 Scope

Manual LinkedIn outreach tracking only. No automation of connection requests, messages, or inbox scraping. The Chrome extension is manual-click only. The backend is the source of truth for stage transitions.
