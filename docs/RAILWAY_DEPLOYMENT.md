� Railway Deployment Guide - EzMsg

Complete guide to deploying the EzMsg messaging protocol management system on Railway.

---

Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **Railway CLI** (optional): `npm i -g @railway/cli`
3. **GitHub Repository**: Push your code to GitHub

---

Quick Deploy (Web UI)

### Step 1: Create New Project

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your repository
5. Select the `ezmsg-new` repository

### Step 2: Add Database Services

Railway will create your first service. Now add the databases:

#### Add PostgreSQL

1. In your project, click **"New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway will provision a PostgreSQL database
3. Note: Connection string is automatically available as `DATABASE_URL`

#### Add Redis

1. Click **"New"** → **"Database"** → **"Add Redis"**
2. Railway will provision a Redis instance
3. Note: Connection string is automatically available as `REDIS_URL`

### Step 3: Deploy Services

Railway's monorepo support will auto-detect the Dockerfiles. You need to create 3 services:

#### Service 1: API (Backend)

1. Click **"New"** → **"GitHub Repo"** → Select your repo
2. In **Settings** → **General**:
   - **Service Name**: `ezmsg-api`
   - **Root Directory**: `/api`
   - **Dockerfile Path**: `api/Dockerfile`
3. In **Settings** → **Networking**:
   - Click **"Generate Domain"** to get a public URL
4. Set **Environment Variables** (see section below)
5. Click **"Deploy"**

#### Service 2: Worker (Background Scheduler)

1. Click **"New"** → **"GitHub Repo"** → Select your repo
2. In **Settings** → **General**:
   - **Service Name**: `ezmsg-worker`
   - **Root Directory**: `/worker`
   - **Dockerfile Path**: `worker/Dockerfile`
3. Set **Environment Variables** (see section below)
4. Click **"Deploy"**

#### Service 3: Web (Frontend)

1. Click **"New"** → **"GitHub Repo"** → Select your repo
2. In **Settings** → **General**:
   - **Service Name**: `ezmsg-web`
   - **Root Directory**: `/web`
   - **Dockerfile Path**: `web/Dockerfile`
3. In **Settings** → **Networking**:
   - Click **"Generate Domain"** to get a public URL
4. Set **Environment Variables** (see section below)
5. Click **"Deploy"**

---

Environment Variables

### API Service (`ezmsg-api`)

```bash
# Database (auto-provided by Railway PostgreSQL)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (auto-provided by Railway Redis)
REDIS_URL=${{Redis.REDIS_URL}}

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Origins (use your Railway frontend domain)
CORS_ORIGINS=["https://your-frontend.up.railway.app"]

# Application Settings
SIMULATION_MODE=false
DEBUG=false
ENVIRONMENT=production

# Twilio (optional - for SMS)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# FCM (optional - for mobile push)
FCM_SERVER_KEY=your_fcm_server_key
```

**Railway Variable References:**
- Use `${{Postgres.DATABASE_URL}}` to reference the PostgreSQL connection
- Use `${{Redis.REDIS_URL}}` to reference Redis
- Railway automatically injects these when you link services

### Worker Service (`ezmsg-worker`)

```bash
# Database (reference from API or PostgreSQL service)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis
REDIS_URL=${{Redis.REDIS_URL}}

# Worker Settings
SIMULATION_MODE=false
POLL_INTERVAL_SECONDS=10
BATCH_SIZE=100
MAX_RETRY_ATTEMPTS=8

# Twilio (same as API)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# FCM (same as API)
FCM_SERVER_KEY=your_fcm_server_key
```

### Web Service (`ezmsg-web`)

```bash
# API URL (use the Railway domain of your API service)
NEXT_PUBLIC_API_URL=https://your-api.up.railway.app

# Build-time variable
API_URL=https://your-api.up.railway.app/v1
```

**Important**: For the web service, you need to use the **public Railway URL** of your API service.

---

Service Linking (Automatic)

Railway automatically makes database connections available through variable references:

1. When you add PostgreSQL, it creates a `Postgres` service
2. Reference it in other services: `${{Postgres.DATABASE_URL}}`
3. Same for Redis: `${{Redis.REDIS_URL}}`
4. For API → Worker/Web communication, use the generated Railway domains

---

Build Configuration

Railway automatically detects:
- **API**: `api/Dockerfile` → Builds Python FastAPI app
- **Worker**: `worker/Dockerfile` → Builds background worker
- **Web**: `web/Dockerfile` → Builds Next.js frontend with multi-stage build

If Railway doesn't auto-detect, manually set:
- **Root Directory**: e.g., `/api`, `/worker`, `/web`
- **Dockerfile Path**: e.g., `api/Dockerfile`

---

Database Migration

After deploying, run migrations:

### Option 1: Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Link to your project
railway link

# Run migration on API service
railway run -s ezmsg-api alembic upgrade head
```

### Option 2: Manual (One-time Script)

1. In Railway dashboard, go to **API service** → **Settings** → **Deployments**
2. Click on latest deployment → **View Logs**
3. Look for startup logs to verify the app started
4. Use Railway's **Shell** feature or run a one-off command:

```bash
railway run -s ezmsg-api python -c "
from app.database.engine import engine
from app.models import Base
import asyncio

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(init_db())
"
```

---

Auto-Deployment

Railway automatically deploys on every push to your main branch:

1. Push to GitHub:
   ```bash
   git add .
   git commit -m "Update for production"
   git push origin main
   ```

2. Railway detects the push and triggers deployments for all services
3. Monitor progress in the Railway dashboard

---

Custom Domains (Optional)

### Add Custom Domain to API

1. Go to **API Service** → **Settings** → **Networking**
2. Click **"Add Custom Domain"**
3. Enter your domain: `api.yourdomain.com`
4. Add DNS records (Railway provides instructions)

### Add Custom Domain to Frontend

1. Go to **Web Service** → **Settings** → **Networking**
2. Click **"Add Custom Domain"**
3. Enter your domain: `app.yourdomain.com`
4. Add DNS records

**Update CORS**: After adding custom domains, update the `CORS_ORIGINS` variable in the API service.

---

Monitoring & Logs

### View Logs

1. Go to any service in Railway dashboard
2. Click **"View Logs"**
3. Real-time logs appear (color-coded by level)

### Metrics

Railway provides:
- **CPU Usage**
- **Memory Usage**
- **Network Traffic**
- **Build Times**

Access these in **Service** → **Metrics**

---

Troubleshooting

### API Service Won't Start

**Check:**
1. DATABASE_URL is set correctly: `${{Postgres.DATABASE_URL}}`
2. JWT_SECRET is at least 32 characters
3. View logs for Python errors

**Common Fixes:**
```bash
# Check if database is accessible
railway run -s ezmsg-api python -c "
import asyncpg
import os
import asyncio
async def test():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    print('Database connected!')
    await conn.close()
asyncio.run(test())
"
```

### Frontend Can't Connect to API

**Check:**
1. `NEXT_PUBLIC_API_URL` is set to the API's Railway domain
2. API service has the frontend domain in `CORS_ORIGINS`
3. API service is running (check status indicator)

**Fix CORS:**
```bash
# In API service environment variables
CORS_ORIGINS=["https://your-frontend.up.railway.app","https://yourdomain.com"]
```

### Worker Not Processing Messages

**Check:**
1. Worker service is running (green indicator)
2. `DATABASE_URL` and `REDIS_URL` are correct
3. Check worker logs for SQL errors

**Fix SQLAlchemy Error:**
The worker has a known SQL syntax issue. If you see errors about `text()`, you need to fix the worker code (see main README).

### Build Failures

**Common Issues:**
- **Out of Memory**: Railway free tier has memory limits. Optimize Dockerfile or upgrade plan.
- **Build Timeout**: Large dependencies. Consider using Railway's build cache.

**Fix:**
```dockerfile
# In Dockerfile, add this to use build cache
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt
```

---

Cost Estimate (Railway Pricing)

Railway pricing (as of 2026):
- **Free Tier**: $5 credit/month, good for testing
- **Hobby Plan**: $5/month + usage
- **Pro Plan**: $20/month + usage

**Estimated Monthly Cost** (Hobby Plan):
- PostgreSQL: ~$5/month (512MB storage)
- Redis: ~$5/month
- 3 Services: ~$5-10/month (depending on usage)
- **Total**: ~$15-20/month for low-medium traffic

**Recommendations:**
- Start with **Hobby Plan** for development
- Upgrade to **Pro** for production with real users
- Use **Custom Domains** with Pro plan

---

Security Checklist

Before going to production:

- [ ] Change `JWT_SECRET` to a secure random string (min 32 chars)
- [ ] Set `SIMULATION_MODE=false`
- [ ] Set `DEBUG=false`
- [ ] Configure proper `CORS_ORIGINS` (no wildcards)
- [ ] Add Twilio credentials for real SMS
- [ ] Enable Railway's **IP Allowlist** if needed
- [ ] Use **Secrets** for sensitive env vars (Railway encrypts these)
- [ ] Set up **backups** for PostgreSQL (Railway Pro feature)

---

� Protocol API Access

After deployment, your Protocol API will be available at:

```
https://your-api.up.railway.app/v1/protocol/start
https://your-api.up.railway.app/v1/protocol/respond
```

**API Key**: Update the hardcoded API key in `api/app/routers/protocol_api.py` or create a database table for API keys.

**Testing:**
```bash
curl -X POST https://your-api.up.railway.app/v1/protocol/start \
  -H "Content-Type: application/json" \
  -H "X-API-Key: iquit0-test-key-12345" \
  -d '{"project_id": 7, "language": "en", "initial_response": "iquit0"}'
```

---

Success!

Your EzMsg application should now be live on Railway!

**Access URLs:**
- **Frontend**: `https://your-web.up.railway.app`
- **API**: `https://your-api.up.railway.app`
- **API Docs**: `https://your-api.up.railway.app/docs` (if DEBUG=true)

**Next Steps:**
1. Import QuitTxt V9 protocol data
2. Create admin user
3. Test protocol flow via Postman
4. Configure Twilio for production SMS

---

Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway)
- [Railway Status](https://status.railway.app)
- [EzMsg GitHub Issues](https://github.com/your-repo/issues)

---

Support

If you encounter issues:

1. **Check Railway Logs**: Service → View Logs
2. **Railway Discord**: Fast community support
3. **GitHub Issues**: Report bugs
4. **Railway Status**: Check for platform issues

---

**Happy Deploying! 🚀**
