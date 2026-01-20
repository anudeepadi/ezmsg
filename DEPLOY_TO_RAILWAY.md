# 🚀 Deploy EzMsg to Railway - Step-by-Step Guide

**Status**: ✅ Ready for Deployment
- Database: ✅ Connected (Supabase PostgreSQL)
- Protocol: ✅ Tested and Working
- API: ✅ 70 Routes Active
- Data: ✅ QuitTxt V9 Imported (63 nodes, 61 templates)

---

## Prerequisites Checklist

Before deploying, ensure you have:

- ✅ Supabase PostgreSQL connection string (from `.env.local`)
- ✅ Redis connection string (optional - can deploy without it)
- ✅ GitHub repository with your code pushed
- ✅ Railway account (sign up at https://railway.app)
- ✅ Test completed successfully (run `python test_protocol_multiday.py`)

---

## Part 1: Railway Project Setup (5 minutes)

### Step 1: Create New Railway Project

1. Go to https://railway.app and sign in
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your `ezmsg-new` repository
5. Railway will detect multiple services - we'll configure them separately

### Step 2: Configure Services

You need to create **3 services**:

1. **API Service** - FastAPI backend
2. **Web Service** - Next.js frontend
3. **Worker Service** - Background message scheduler (optional for MVP)

---

## Part 2: API Service Configuration (10 minutes)

### Step 1: Create API Service

1. In your Railway project, click **"+ New Service"**
2. Select **"GitHub Repo"** → Choose your repository
3. Name it: `ezmsg-api`

### Step 2: Configure Build Settings

Go to **Settings** → **Build**:

```yaml
Root Directory: api
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Step 3: Add Environment Variables

Go to **Variables** tab and add these (copy from your `.env.local`):

```bash
# Database (REQUIRED)
DATABASE_URL=postgresql+asyncpg://postgres.nkxewmxszqtjaeveimou:Factorysmokeloud2%24@aws-1-us-east-1.pooler.supabase.com:5432/postgres

# Redis (OPTIONAL - can omit if SSL errors persist)
REDIS_URL=rediss://default:bRjLQBRYXcs5Pt1H2PNgZA7HFFDqIhaZ@redis-16847.c278.us-east-1-4.ec2.cloud.redislabs.com:16847

# JWT Authentication (REQUIRED)
JWT_SECRET=YOUR_SECURE_SECRET_HERE_MIN_32_CHARS
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application Settings (REQUIRED)
ENVIRONMENT=production
DEBUG=false
SIMULATION_MODE=false

# Supabase (OPTIONAL - for direct Supabase client usage)
SUPABASE_URL=https://nkxewmxszqtjaeveimou.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5reGV3bXhzenF0amFldmVpbW91Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg5MzczNzAsImV4cCI6MjA4NDUxMzM3MH0.Rk2W9cqM77M36gGsmx1r9DWOFze7JkKd6Vnkzfxk_7E
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5reGV3bXhzenF0amFldmVpbW91Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODkzNzM3MCwiZXhwIjoyMDg0NTEzMzcwfQ.7MQxPg8RHMxahuE1sTC-hmN6TfARoE_qKIVVzd13384
```

**IMPORTANT CHANGES:**

1. **JWT_SECRET**: Generate a new secure secret:
   ```bash
   openssl rand -base64 48
   ```
   Copy the output and use it as JWT_SECRET

2. **CORS_ORIGINS**: After deployment, add your Railway domains:
   ```bash
   # You'll update this after getting your domains
   CORS_ORIGINS=["https://your-web-app.railway.app","https://localhost:3000"]
   ```

### Step 4: Deploy API

1. Railway will automatically deploy
2. Wait for build to complete (2-3 minutes)
3. Check logs for any errors
4. Once deployed, you'll see: **"Uvicorn running on..."**

### Step 5: Test API

1. Copy your API URL from Railway (e.g., `https://ezmsg-api-production.up.railway.app`)
2. Test the health endpoint:
   ```bash
   curl https://your-api-url.railway.app/health
   ```
3. You should see: `{"status": "healthy"}`

---

## Part 3: Web Service Configuration (5 minutes)

### Step 1: Create Web Service

1. Click **"+ New Service"** again
2. Select same GitHub repository
3. Name it: `ezmsg-web`

### Step 2: Configure Build Settings

Go to **Settings** → **Build**:

```yaml
Root Directory: web
Build Command: npm install && npm run build
Start Command: npm start
```

### Step 3: Add Environment Variable

Go to **Variables** tab:

```bash
# Replace with your actual API URL from Part 2, Step 5
NEXT_PUBLIC_API_URL=https://your-api-url.railway.app
```

### Step 4: Deploy Web

1. Railway will automatically deploy
2. Wait for build (3-5 minutes)
3. Check logs for any errors

### Step 5: Update CORS

Now that you have your web URL, go back to **API Service** → **Variables**:

```bash
# Update CORS_ORIGINS to include your web URL
CORS_ORIGINS=["https://your-web-url.railway.app"]
```

Save and redeploy API service.

---

## Part 4: Worker Service (Optional - for Scheduler)

The worker sends scheduled messages based on timing elements.

### Step 1: Create Worker Service

1. Click **"+ New Service"**
2. Select same GitHub repository
3. Name it: `ezmsg-worker`

### Step 2: Configure Build Settings

```yaml
Root Directory: api
Build Command: pip install -r requirements.txt
Start Command: python -m app.worker.scheduler
```

### Step 3: Add Environment Variables

Copy **all environment variables** from the API service (they need to be the same).

### Step 4: Deploy Worker

Railway will deploy the worker service automatically.

---

## Part 5: Post-Deployment Verification (10 minutes)

### Test 1: API Health Check

```bash
curl https://your-api-url.railway.app/health
```

Expected: `{"status": "healthy"}`

### Test 2: Test Protocol API

```bash
curl -X POST https://your-api-url.railway.app/v1/protocol/start \
  -H "X-API-Key: iquit0-test-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 7,
    "language": "en",
    "initial_response": "iquit0"
  }'
```

Expected: JSON response with session_id and first message

### Test 3: Admin Login

1. Open: `https://your-web-url.railway.app`
2. Login with:
   - Email: `admin@example.com`
   - Password: `admin123`
3. Navigate to Projects → QuitTxt V9
4. Verify you can see the protocol structure

### Test 4: Database Connection

```bash
curl https://your-api-url.railway.app/v1/admin/projects
```

Expected: List of projects including QuitTxt V9

---

## Part 6: Production Hardening

### Security Updates (CRITICAL)

1. **Change Default Admin Password**:
   - Login to admin panel
   - Go to Settings → Change Password
   - Use a strong password

2. **Update API Key**:
   In `api/app/routers/protocol_api.py`, change line 22:
   ```python
   # OLD (development):
   API_KEY = "iquit0-test-key-12345"

   # NEW (production - use environment variable):
   import os
   API_KEY = os.getenv("PROTOCOL_API_KEY", "iquit0-test-key-12345")
   ```

   Then add to Railway API variables:
   ```bash
   PROTOCOL_API_KEY=YOUR_SECURE_RANDOM_KEY_HERE
   ```

   Generate a secure key:
   ```bash
   openssl rand -hex 32
   ```

3. **Enable Rate Limiting** (recommended):
   Add to `api/app/main.py` (if not already present)

### Monitoring Setup

1. **Railway Metrics**:
   - Go to each service → Metrics tab
   - Monitor: CPU, Memory, Request Rate

2. **Set Up Alerts**:
   - Railway → Project Settings → Notifications
   - Enable Slack/Discord webhooks for deployment failures

3. **Database Monitoring**:
   - Supabase Dashboard → Database → Performance
   - Monitor: Connection count, Query performance

### Backup Strategy

1. **Supabase Backups**:
   - Supabase Dashboard → Settings → Database → Backups
   - Daily backups enabled by default
   - Test restore process

2. **Environment Variables Backup**:
   - Save all Railway environment variables locally
   - Store securely (password manager or encrypted file)

---

## Part 7: Common Issues & Solutions

### Issue 1: API Won't Start

**Symptoms**: Build succeeds but service crashes

**Solution**:
- Check logs: `ModuleNotFoundError` or `ImportError`
- Verify `requirements.txt` includes all dependencies
- Ensure `ROOT_DIRECTORY` is set to `api`

### Issue 2: Database Connection Fails

**Symptoms**: `ConnectionRefusedError` or `TimeoutError`

**Solution**:
- Verify `DATABASE_URL` is correct (must use Session Pooler URL)
- Check password is URL-encoded (`$` → `%24`)
- Ensure Supabase allows Railway IP addresses (usually automatic)

### Issue 3: CORS Errors

**Symptoms**: Web app can't reach API

**Solution**:
```bash
# Update CORS_ORIGINS in API service variables:
CORS_ORIGINS=["https://your-web-url.railway.app","http://localhost:3000"]
```

### Issue 4: Redis Errors (Non-Critical)

**Symptoms**: `SSL: record layer failure`

**Solution**:
- Redis is only used for caching
- Can safely omit `REDIS_URL` for MVP
- Or try Railway's Redis addon: `railway add redis`

### Issue 5: Next.js Build Fails

**Symptoms**: `MODULE_NOT_FOUND` during build

**Solution**:
- Ensure `package.json` and `package-lock.json` are committed
- Check Node version (Railway uses latest LTS)
- Verify `ROOT_DIRECTORY` is set to `web`

---

## Part 8: Scaling & Performance

### Current Limits (Free Tier)

Railway free tier includes:
- $5 credit per month
- ~500 hours of compute
- Sufficient for:
  - ~100-200 participants
  - ~1000 messages per day
  - Development and testing

### When to Upgrade

Consider upgrading when:
- More than 100 active participants
- Sending 1000+ messages per day
- Need higher uptime guarantees
- Want custom domains

### Performance Optimization

1. **Database Connection Pooling** (already configured):
   - Supabase Session Pooler handles this
   - Max 15 concurrent connections per service

2. **API Response Caching**:
   - Enable Redis if needed
   - Or use Railway Redis addon

3. **Static Asset CDN**:
   - Next.js automatically optimizes images
   - Consider Cloudflare for additional caching

---

## Part 9: Deployment Checklist

Use this checklist for each deployment:

### Pre-Deployment
- [ ] Code tested locally
- [ ] All tests passing
- [ ] Environment variables documented
- [ ] Database migrations ready (if any)
- [ ] Breaking changes documented

### During Deployment
- [ ] API service deployed
- [ ] Web service deployed
- [ ] Worker service deployed (if using)
- [ ] Environment variables updated
- [ ] CORS configured correctly

### Post-Deployment
- [ ] Health check passes
- [ ] Admin login works
- [ ] Protocol API tested
- [ ] Logs reviewed (no critical errors)
- [ ] Database connections stable
- [ ] Performance metrics normal

### Production Security
- [ ] Default passwords changed
- [ ] API keys rotated
- [ ] JWT secret is secure
- [ ] Rate limiting enabled
- [ ] Monitoring configured
- [ ] Backup tested

---

## Part 10: Quick Reference

### Your Deployment URLs

After deployment, save these URLs:

```bash
API URL: https://_____________.railway.app
Web URL: https://_____________.railway.app
Worker URL: https://_____________.railway.app (if using)
```

### Admin Credentials

```
Email: admin@example.com
Password: _____________ (change after first login!)
```

### API Keys

```
Admin API: Bearer <JWT token from login>
Protocol API: _____________ (change from default!)
```

### Support Resources

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Supabase Docs: https://supabase.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com
- Next.js Docs: https://nextjs.org/docs

---

## 🎉 Deployment Complete!

Your EzMsg system is now live on Railway with:

- ✅ Supabase PostgreSQL database
- ✅ QuitTxt V9 protocol with 63 nodes
- ✅ Protocol API for external integrations
- ✅ Admin UI for management
- ✅ Multi-day message scheduling

**Next Steps:**
1. Change all default passwords and API keys
2. Test with real participants (small group first)
3. Monitor for 24-48 hours
4. Scale as needed

**Questions?** Check the docs or Railway Discord for help!

---

**Deployment Date**: _____________
**Deployed By**: _____________
**Version**: v1.0.0
