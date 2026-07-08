# Backend

FastAPI + SQLAlchemy + Alembic API for NetworkPilot CRM.

## Development

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## Testing

```bash
pytest
```

## Deployment (Render)

### Prerequisites
- Render account
- Supabase project with database

### Steps
1. Connect GitHub repo to Render
2. Create a new Web Service
3. Set build command: `pip install -e .`
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   - `DATABASE_URL` - Supabase Postgres connection string. Plain `postgresql://`,
     `postgres://`, and `postgresql+asyncpg://` URLs are accepted; include
     `?sslmode=require` for hosted Supabase connections.
   - `SUPABASE_URL` - Supabase project URL
   - `SUPABASE_ANON_KEY` - Supabase anon key
   - `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
   - `JWT_SECRET` - Supabase JWT secret
   - `ENVIRONMENT` - `production`
   - `CORS_ORIGINS` - Your frontend URL (e.g., `https://your-app.vercel.app`)

### Running Migrations
After first deploy, run migration via Render Shell:
```bash
alembic upgrade head
```

### Health Check
Once deployed, verify: `https://your-app.onrender.com/health`
