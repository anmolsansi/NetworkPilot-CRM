# Architecture

## System Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React Web     │────▶│   FastAPI       │────▶│  Supabase       │
│   App           │     │   Backend       │     │  Postgres       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              ▲                         
                              │                         
┌─────────────────┐           │                         
│   Chrome        │───────────┘                         
│   Extension     │                                     
└─────────────────┘                                     
```

## Surfaces

### Frontend (React Web App)
- Dashboard for due follow-ups
- People list with filters
- Person detail with activity timeline
- Message templates
- Workspace settings
- Auth via Supabase JS client

### Backend (FastAPI)
- REST API at `/api/v1`
- JWT auth via Supabase
- SQLAlchemy ORM
- Alembic migrations
- Stage transition logic

### Chrome Extension (React MV3)
- Popup-only UI (no content scripts)
- Quick save/update LinkedIn profiles
- Template copy-to-clipboard
- Reads active tab URL

## Auth Flow

1. User signs up/logs in via Supabase (frontend)
2. Supabase returns JWT access token
3. Frontend/extension sends token in `Authorization: Bearer <token>`
4. Backend verifies JWT, extracts user ID
5. Backend bootstraps internal user record on first request

## Stage Machine

```
invite_sent → invite_pending → accepted → first_message_sent
                                             ↓
                                    waiting_for_reply → replied
                                             ↓
                                    follow_up_1_sent → follow_up_2_sent
                                             ↓
                                        no_reply
```

## Key Principles

1. **Backend is source of truth** — All transitions go through API
2. **Workspace isolation** — All data scoped to workspace
3. **Soft deletes** — Never hard delete people or templates
4. **Manual only** — No automation of LinkedIn actions
