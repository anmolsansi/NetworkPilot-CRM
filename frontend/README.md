# Frontend

React + Vite + TypeScript web app for NetworkPilot CRM.

## Development

```bash
npm install
cp .env.example .env
npm run dev
```

## Build

```bash
npm run build
```

## Deployment (Vercel)

### Prerequisites
- Vercel account
- Deployed backend on Render

### Steps
1. Connect GitHub repo to Vercel
2. Set root directory to `frontend`
3. Framework preset: Vite
4. Build command: `npm run build`
5. Output directory: `dist`
6. Add environment variables:
   - `VITE_SUPABASE_URL` - Supabase project URL
   - `VITE_SUPABASE_ANON_KEY` - Supabase anon key
   - `VITE_API_BASE_URL` - Your backend URL (e.g., `https://your-app.onrender.com/api/v1`)

### Environment Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_SUPABASE_URL` | Supabase project URL | `https://xxx.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon key | `eyJxxx...` |
| `VITE_API_BASE_URL` | Backend API URL | `https://your-app.onrender.com/api/v1` |

### Post-Deploy
1. Update backend `CORS_ORIGINS` to include your Vercel URL
2. Update Supabase Auth redirect URLs to include your Vercel URL
