# EzMsg — Railway Deployment Guide

Deploy EzMsg to Railway with managed PostgreSQL and Redis.

## Prerequisites

- [Railway account](https://railway.app) (free tier or paid)
- GitHub repo connected to Railway
- External databases set up (see below) OR Railway-managed databases

## Architecture on Railway

| Service | Source | Port | Notes |
|---------|--------|------|-------|
| **ezmsg-api** | `api/Dockerfile` | $PORT | REST API, auto-assigned by Railway |
| **ezmsg-worker** | `worker/Dockerfile` | none | Background process, no HTTP port |
| **ezmsg-web** | `web/Dockerfile` | 3000 | Next.js admin dashboard |
| **PostgreSQL** | Railway plugin or Supabase | 5432 | Primary data store |
| **Redis** | Railway plugin or Upstash | 6379 | Session cache + rate limiting |

## Step 1: Create Railway Project (2 min)

1. Go to [railway.app/new](https://railway.app/new)
2. Click **"Deploy from GitHub repo"**
3. Select your `ezmsg-new` repository
4. Railway creates the first service (API) automatically

## Step 2: Add Database Services (3 min)

**Option A: Railway Managed (Simplest)**
1. In your Railway project, click **"+ New"** > **"Database"** > **PostgreSQL**
2. Click **"+ New"** > **"Database"** > **Redis**
3. Use Railway variable references: `${{Postgres.DATABASE_URL}}` and `${{Redis.REDIS_URL}}`

**Option B: External (Free Tier)**
- Supabase PostgreSQL: paste your connection string directly
- Upstash Redis: paste your connection string directly

## Step 3: Configure API Service (5 min)

In the API service settings:

**Build:**
- Builder: Dockerfile
- Dockerfile path: `api/Dockerfile`
- Watch paths: `api/**`

**Deploy:**
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`

**Environment Variables** (set in Railway dashboard > Variables):

```
# Required
DATABASE_URL=<your postgres connection string>
REDIS_URL=<your redis connection string>
ENVIRONMENT=production
JWT_SECRET=<generate: openssl rand -base64 48>
PROTOCOL_API_KEY=<generate: openssl rand -hex 24>
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=<strong password>

# Application
SIMULATION_MODE=false
DEBUG=false
CORS_ORIGINS=["https://your-web-service.up.railway.app"]
```

Generate secrets locally:
```bash
openssl rand -base64 48   # JWT_SECRET
openssl rand -hex 24      # PROTOCOL_API_KEY
```

## Step 4: Add Worker Service (3 min)

1. In Railway project, click **"+ New"** > **"GitHub Repo"** > select same repo
2. Rename the service to `ezmsg-worker`
3. Configure:
   - Dockerfile path: `worker/Dockerfile`
   - Watch paths: `worker/**`
   - **No port** — this is a background process
4. Set environment variables:

```
DATABASE_URL=<same as API>
REDIS_URL=<same as API>
SIMULATION_MODE=false
```

## Step 5: Add Web Service (3 min)

1. Click **"+ New"** > **"GitHub Repo"** > select same repo
2. Rename to `ezmsg-web`
3. Configure:
   - Dockerfile path: `web/Dockerfile`
   - Port: 3000
4. Set environment variables:

```
NEXT_PUBLIC_API_URL=https://your-api-service.up.railway.app
```

## Step 6: Generate Domains & Test (2 min)

1. For API service: **Settings > Networking > Generate Domain**
2. For Web service: **Settings > Networking > Generate Domain**
3. Worker does NOT need a domain

**Test the deployment:**
```bash
# Health check
curl https://your-api.up.railway.app/health

# Start a protocol session
curl -X POST https://your-api.up.railway.app/v1/protocol/start \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_PROTOCOL_API_KEY" \
  -d '{"project_id": 7, "language": "en"}'
```

## Step 7: Import Protocol Data

SSH into the API service or run the import script:
```bash
# Via Railway CLI
railway run -s ezmsg-api -- python scripts/import_quittxt_v9_protocol.py
```

## Post-Deployment Checklist

- [ ] Health check returns `{"status": "healthy"}`
- [ ] Admin login works at web dashboard
- [ ] Protocol start/respond endpoints work with API key
- [ ] Worker is running (check Railway logs)
- [ ] Update `CORS_ORIGINS` with actual web domain
- [ ] Set `SIMULATION_MODE=false` when ready for real delivery
- [ ] Configure Twilio credentials for SMS
- [ ] Configure Firebase credentials for push notifications
- [ ] Set up custom domain (optional)

## Troubleshooting

**API won't start:**
- Check `DATABASE_URL` format — must use `postgresql+asyncpg://`
- Verify `JWT_SECRET` is set and at least 32 characters

**Worker not processing messages:**
- Confirm `SIMULATION_MODE=false` if expecting real delivery
- Check worker logs in Railway dashboard
- Verify DATABASE_URL and REDIS_URL are correct

**CORS errors from frontend:**
- Update `CORS_ORIGINS` to include your web service domain
- Must be JSON array: `["https://your-web.up.railway.app"]`

## Cost Estimates

| Tier | Monthly | Capacity |
|------|---------|----------|
| Free / Hobby | $0-5 | Development, testing |
| Starter | ~$10-20 | Small study (<100 participants) |
| Production | ~$30-50 | Full study (1000+ participants) |
