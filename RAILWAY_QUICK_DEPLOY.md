# ⚡ Railway Quick Deploy - 30 Minute Checklist

**Print this page or keep it open while deploying!**

---

## Before You Start

Have these ready:

```bash
✅ Supabase DATABASE_URL (from .env.local line 20)
✅ Redis REDIS_URL (from .env.local line 27) - optional
✅ GitHub repository URL
✅ Railway account (railway.app)
```

---

## Step 1: Railway Project (2 min)

1. [ ] Go to https://railway.app → Sign in
2. [ ] Click "New Project"
3. [ ] Select "Deploy from GitHub repo"
4. [ ] Choose `ezmsg-new` repository

---

## Step 2: API Service (8 min)

### Create Service
1. [ ] Click "+ New Service" → "GitHub Repo"
2. [ ] Name: `ezmsg-api`

### Configure Build
**Settings → Build:**
```
Root Directory: api
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Add Variables
**Variables tab - paste these:**

```bash
DATABASE_URL=postgresql+asyncpg://postgres.nkxewmxszqtjaeveimou:Factorysmokeloud2%24@aws-1-us-east-1.pooler.supabase.com:5432/postgres

JWT_SECRET=GENERATE_NEW_SECRET_HERE
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

ENVIRONMENT=production
DEBUG=false
SIMULATION_MODE=false

SUPABASE_URL=https://nkxewmxszqtjaeveimou.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5reGV3bXhzenF0amFldmVpbW91Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg5MzczNzAsImV4cCI6MjA4NDUxMzM3MH0.Rk2W9cqM77M36gGsmx1r9DWOFze7JkKd6Vnkzfxk_7E
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5reGV3bXhzenF0amFldmVpbW91Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODkzNzM3MCwiZXhwIjoyMDg0NTEzMzcwfQ.7MQxPg8RHMxahuE1sTC-hmN6TfARoE_qKIVVzd13384
```

### Generate JWT_SECRET
**Run this locally:**
```bash
openssl rand -base64 48
```
**Copy output and replace `GENERATE_NEW_SECRET_HERE`**

### Deploy & Test
3. [ ] Click "Deploy" (wait 2-3 min)
4. [ ] Copy API URL: `https://_________.railway.app`
5. [ ] Test: `curl https://YOUR_API_URL/health`
6. [ ] Should see: `{"status": "healthy"}`

---

## Step 3: Web Service (5 min)

### Create Service
1. [ ] Click "+ New Service" → "GitHub Repo"
2. [ ] Name: `ezmsg-web`

### Configure Build
**Settings → Build:**
```
Root Directory: web
Start Command: npm start
```

### Add Variables
**Variables tab:**
```bash
NEXT_PUBLIC_API_URL=https://YOUR_API_URL_FROM_STEP_2
```

### Deploy & Test
3. [ ] Click "Deploy" (wait 3-5 min)
4. [ ] Copy Web URL: `https://_________.railway.app`
5. [ ] Open Web URL in browser
6. [ ] Should see login page

---

## Step 4: Update CORS (2 min)

1. [ ] Go back to **API Service** → Variables
2. [ ] Add new variable:
```bash
CORS_ORIGINS=["https://YOUR_WEB_URL_FROM_STEP_3"]
```
3. [ ] Click "Deploy" to restart API

---

## Step 5: Test Everything (5 min)

### Test 1: Admin Login
1. [ ] Go to Web URL
2. [ ] Login: `admin@example.com` / `admin123`
3. [ ] Should see admin dashboard

### Test 2: Protocol API
**Run this locally (replace YOUR_API_URL):**
```bash
curl -X POST https://YOUR_API_URL/v1/protocol/start \
  -H "X-API-Key: iquit0-test-key-12345" \
  -H "Content-Type: application/json" \
  -d '{"project_id": 7, "language": "en", "initial_response": "iquit0"}'
```
4. [ ] Should return JSON with session_id

### Test 3: Check Logs
5. [ ] API Service → Logs tab
6. [ ] Should see: "Application startup complete"
7. [ ] No error messages

---

## Step 6: Security Hardening (5 min)

### Change Admin Password
1. [ ] Login to Web UI
2. [ ] Settings → Change Password
3. [ ] Use strong password

### Update API Key
**Edit `api/app/routers/protocol_api.py` line 22:**
```python
import os
API_KEY = os.getenv("PROTOCOL_API_KEY", "iquit0-test-key-12345")
```

**Generate new API key:**
```bash
openssl rand -hex 32
```

**Add to API Service Variables:**
```bash
PROTOCOL_API_KEY=YOUR_NEW_KEY_HERE
```

4. [ ] Commit and push changes
5. [ ] Railway auto-deploys

---

## Step 7: Optional - Worker Service (5 min)

**Only if you need background message scheduler**

### Create Service
1. [ ] Click "+ New Service" → "GitHub Repo"
2. [ ] Name: `ezmsg-worker`

### Configure Build
**Settings → Build:**
```
Root Directory: api
Start Command: python -m app.worker.scheduler
```

### Add Variables
3. [ ] Copy ALL variables from API Service
4. [ ] Paste into Worker Service variables

5. [ ] Click "Deploy"

---

## ✅ Deployment Complete!

### Your URLs (save these!)

```
API: https://_________________.railway.app
Web: https://_________________.railway.app
```

### Admin Credentials (change these!)

```
Email: admin@example.com
Password: _______________ (CHANGE THIS!)
```

### API Keys (change these!)

```
Protocol API Key: _______________ (CHANGE THIS!)
```

---

## 🔥 Quick Commands

### Test API Health
```bash
curl https://YOUR_API_URL/health
```

### Test Protocol Start
```bash
curl -X POST https://YOUR_API_URL/v1/protocol/start \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"project_id": 7, "language": "en", "initial_response": "iquit0"}'
```

### View Logs
```bash
# In Railway Dashboard:
Service → Logs tab
```

### Restart Service
```bash
# In Railway Dashboard:
Service → Settings → Restart
```

---

## 🆘 Common Issues

### "Module not found"
- Check Root Directory is correct (`api` or `web`)
- Check requirements.txt / package.json committed

### "Connection refused"
- Check DATABASE_URL is correct
- Verify password is URL-encoded (`$` → `%24`)

### "CORS error"
- Update CORS_ORIGINS in API variables
- Include your Web URL

### "Build failed"
- Check logs for specific error
- Verify all dependencies in requirements.txt
- Try local build first

---

## 📊 Post-Deployment Monitoring

### First Hour
- [ ] Check all service logs (no errors)
- [ ] Test admin login
- [ ] Test Protocol API
- [ ] Verify database connections

### First Day
- [ ] Monitor Railway metrics (CPU, Memory)
- [ ] Check Supabase dashboard (connection count)
- [ ] Test with 1-2 real participants
- [ ] Review logs for warnings

### First Week
- [ ] Verify scheduled messages send correctly
- [ ] Monitor message delivery rates
- [ ] Check database performance
- [ ] Review error rates

---

## 🎯 Next Steps

1. [ ] Create test participant
2. [ ] Test full protocol flow
3. [ ] Set up monitoring alerts
4. [ ] Document custom domains (if needed)
5. [ ] Plan scaling strategy

---

**Deployment Date**: ___________
**Deployed By**: ___________
**Checklist Completed**: [ ]
