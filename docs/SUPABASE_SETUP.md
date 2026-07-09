# Supabase Setup

## Creating a Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Click "New Project"
3. Enter project name: `networkpilot-crm`
4. Enter a secure database password (save it)
5. Choose a region close to your users
6. Click "Create new project"

## Required Values

After project creation, go to **Settings > API** and copy:

| Value | Where Used | Description |
|-------|------------|-------------|
| `SUPABASE_URL` | Frontend, Extension | Project URL (e.g., `https://xxx.supabase.co`) |
| `SUPABASE_ANON_KEY` | Frontend, Extension | Public anonymous key |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend only | Secret admin key (never expose to frontend) |
| `DATABASE_URL` | Backend | Shared Pooler session-mode Postgres connection string |

## Getting Database URL

1. Go to **Connect** > **Connection pooling**
2. Select **Session mode**
3. Copy the Shared Pooler connection string
4. Replace `[YOUR-PASSWORD]` with your database password
5. Format: `postgres://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-[REGION].pooler.supabase.com:5432/postgres?sslmode=require`

## Auth Configuration

### Enable Email and Google Auth
1. Go to **Authentication > Providers**
2. Ensure "Email" is enabled
3. Enable **Google**
4. Add your Google OAuth client ID and secret
5. Configure email templates if desired

### Redirect URLs
Add every frontend and extension redirect URL under **Authentication > URL Configuration**:

- Local web app: `http://localhost:5173/auth/callback`
- Production web app: `https://your-app.vercel.app/auth/callback`
- Chrome extension OAuth: `https://[EXTENSION_ID].chromiumapp.org/auth`

For unpacked local extension testing, Chrome shows the extension ID at
`chrome://extensions/` after loading `extension/dist`.

### JWT Settings
- The `jwt_secret` is in **Settings > API > JWT Settings**
- Backend uses this to verify tokens
- Found in `supabase.auth.jwt_secret` or as `JWT_SECRET` env var

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgres://postgres.xxx:password@aws-[REGION].pooler.supabase.com:5432/postgres?sslmode=require
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJxxx...
SUPABASE_SERVICE_ROLE_KEY=eyJxxx...
JWT_SECRET=your-jwt-secret
```

### Frontend (.env)
```
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJxxx...
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### Extension (.env)
```
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJxxx...
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Local vs Hosted

### Local Development
- Use Supabase CLI for local dev (optional)
- Or use hosted Supabase project
- Set `DATABASE_URL` to local Postgres or hosted Supabase

### Production
- Use hosted Supabase project
- Use the IPv4-compatible Shared Pooler session-mode URL on Render. Supabase
  direct hosts (`db.xxx.supabase.co`) require IPv6 unless the project has the
  IPv4 add-on.
- Never commit `.env` files
- Use Render/Vercel environment variables

## Security Notes

- Never commit `SUPABASE_SERVICE_ROLE_KEY` to git
- Never expose `SUPABASE_SERVICE_ROLE_KEY` to frontend or extension
- Backend uses service role for admin operations
- Frontend/extension use anon key for public operations
- JWT verification uses `JWT_SECRET`
- Frontend and extension both use Supabase Google OAuth. Data sync is account
  scoped by the Supabase JWT `sub` claim and workspace membership checks in the
  backend.
