# Deployment Guide

## Overview

NetworkPilot CRM is deployed as:
- **Backend**: Render (FastAPI)
- **Frontend**: Vercel (React)
- **Extension**: Chrome (Unpacked)
- **Database**: Supabase (Postgres)

## Prerequisites

1. GitHub account with repo access
2. Render account (free tier available)
3. Vercel account (free tier available)
4. Supabase project

## Step 1: Set Up Supabase

1. Create Supabase project at [supabase.com](https://supabase.com)
2. Go to Settings > API and copy:
   - Project URL
   - Anon key
   - Service role key
   - JWT secret
3. Go to Settings > Database and copy connection string

See [SUPABASE_SETUP.md](SUPABASE_SETUP.md) for details.

## Step 2: Deploy Backend to Render

1. Connect GitHub repo to Render
2. Create new Web Service
3. Configure:
   - **Name**: `networkpilot-api`
   - **Runtime**: Python
   - **Build Command**: `pip install -e .`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables:
   ```
   DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres?sslmode=require
   SUPABASE_URL=https://xxx.supabase.co
   SUPABASE_ANON_KEY=eyJxxx...
   SUPABASE_SERVICE_ROLE_KEY=eyJxxx...
   JWT_SECRET=your-jwt-secret
   ENVIRONMENT=production
   CORS_ORIGINS=https://your-app.vercel.app
   ```
5. Deploy
6. Run migration via Render Shell:
   ```bash
   alembic upgrade head
   ```
7. Verify: `https://your-app.onrender.com/health`

## Step 3: Deploy Frontend to Vercel

1. Connect GitHub repo to Vercel
2. Configure:
   - **Root Directory**: `frontend`
   - **Framework**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
3. Add environment variables:
   ```
   VITE_SUPABASE_URL=https://xxx.supabase.co
   VITE_SUPABASE_ANON_KEY=eyJxxx...
   VITE_API_BASE_URL=https://your-app.onrender.com/api/v1
   ```
4. Deploy
5. Update backend `CORS_ORIGINS` to include Vercel URL
6. Update Supabase Auth redirect URLs

## Step 4: Install Extension

1. Follow [EXTENSION_INSTALL.md](EXTENSION_INSTALL.md)
2. Use deployed backend URL
3. Get access token from web app DevTools

## Environment Variables

### Backend
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anonymous key |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key |
| `JWT_SECRET` | Supabase JWT secret |
| `ENVIRONMENT` | `development` or `production` |
| `CORS_ORIGINS` | Comma-separated allowed origins |

### Frontend
| Variable | Description |
|----------|-------------|
| `VITE_SUPABASE_URL` | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anonymous key |
| `VITE_API_BASE_URL` | Backend API URL |

## Post-Deployment

1. Create a workspace in the web app
2. Note the workspace ID from the URL
3. Configure extension with workspace ID
4. Test the full flow

## Troubleshooting

### Backend won't start
- Check environment variables are set
- Verify `DATABASE_URL` points to a reachable primary Postgres host. For
  Supabase on Render, use the IPv4-compatible pooler URL if the direct database
  host is not reachable from Render.
- Include `?sslmode=require` for hosted Supabase connections. The backend
  accepts plain `postgresql://` URLs and adapts them for asyncpg at runtime.
- Check Render logs

### Frontend can't connect to backend
- Verify `VITE_API_BASE_URL` is correct
- Check backend CORS_ORIGINS includes frontend URL
- Ensure backend is running

### Extension not working
- Verify API URL is correct
- Check access token is valid
- Ensure workspace ID is set
