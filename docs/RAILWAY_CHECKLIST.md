Railway Deployment Checklist

Quick reference checklist for deploying EzMsg to Railway.

---

## Before You Start

- [ ] Railway account created ([railway.app](https://railway.app))
- [ ] Code pushed to GitHub repository
- [ ] Railway CLI installed (optional): `npm i -g @railway/cli`

---

## Step 1: Create Project & Databases

- [ ] Create new Railway project
- [ ] Add PostgreSQL database service
- [ ] Add Redis database service
- [ ] Note the service names: `Postgres`, `Redis`

---

## Step 2: Deploy API Service

- [ ] Create new service from GitHub repo
- [ ] Set service name: `ezmsg-api`
- [ ] Set root directory: `/api`
- [ ] Set dockerfile path: `api/Dockerfile`
- [ ] Generate public domain
- [ ] **Copy API domain URL** (you'll need this for Web service)

### Environment Variables:
- [ ] `DATABASE_URL` = `${{Postgres.DATABASE_URL}}`
- [ ] `REDIS_URL` = `${{Redis.REDIS_URL}}`
- [ ] `JWT_SECRET` = (generate: `openssl rand -base64 48`)
- [ ] `JWT_ALGORITHM` = `HS256`
- [ ] `ACCESS_TOKEN_EXPIRE_MINUTES` = `30`
- [ ] `REFRESH_TOKEN_EXPIRE_DAYS` = `7`
- [ ] `CORS_ORIGINS` = `["https://your-web-domain.up.railway.app"]` (update after Web deployed)
- [ ] `SIMULATION_MODE` = `false` (or `true` for testing)
- [ ] `DEBUG` = `false`
- [ ] `ENVIRONMENT` = `production`
- [ ] Deploy the service

---

## Step 3: Deploy Worker Service

- [ ] Create new service from GitHub repo
- [ ] Set service name: `ezmsg-worker`
- [ ] Set root directory: `/worker`
- [ ] Set dockerfile path: `worker/Dockerfile`

### Environment Variables:
- [ ] `DATABASE_URL` = `${{Postgres.DATABASE_URL}}`
- [ ] `REDIS_URL` = `${{Redis.REDIS_URL}}`
- [ ] `SIMULATION_MODE` = `false`
- [ ] `POLL_INTERVAL_SECONDS` = `10`
- [ ] `BATCH_SIZE` = `100`
- [ ] `MAX_RETRY_ATTEMPTS` = `8`
- [ ] Deploy the service

---

## Step 4: Deploy Web Service

- [ ] Create new service from GitHub repo
- [ ] Set service name: `ezmsg-web`
- [ ] Set root directory: `/web`
- [ ] Set dockerfile path: `web/Dockerfile`
- [ ] Generate public domain
- [ ] **Copy Web domain URL**

### Environment Variables:
- [ ] `NEXT_PUBLIC_API_URL` = (paste API domain from Step 2)
- [ ] `API_URL` = (paste API domain from Step 2 + `/v1`)
- [ ] Deploy the service

---

## Step 5: Update CORS

- [ ] Go back to API service
- [ ] Update `CORS_ORIGINS` environment variable
- [ ] Add Web domain: `["https://your-web-domain.up.railway.app"]`
- [ ] Redeploy API service (automatic)

---

## Step 6: Database Setup

### Option A: Railway CLI
```bash
railway link
railway run -s ezmsg-api alembic upgrade head
```

### Option B: Manual Script
- [ ] In API service, go to Deployments → Shell
- [ ] Run database initialization script (see RAILWAY_DEPLOYMENT.md)

---

## Step 7: Import Protocol Data

- [ ] Access frontend: `https://your-web-domain.up.railway.app`
- [ ] Login with admin credentials
- [ ] Import QuitTxt V9 protocol
- [ ] Verify nodes and templates are loaded

---

## Step 8: Test Protocol API

```bash
curl -X POST https://your-api-domain.up.railway.app/v1/protocol/start \
  -H "Content-Type: application/json" \
  -H "X-API-Key: iquit0-test-key-12345" \
  -d '{"project_id": 7, "language": "en", "initial_response": "iquit0"}'
```

- [ ] Verify response with session_id
- [ ] Test protocol flow with `/protocol/respond`

---

## Optional: Production Configuration

### Twilio (for SMS)
- [ ] Add `TWILIO_ACCOUNT_SID` to API & Worker
- [ ] Add `TWILIO_AUTH_TOKEN` to API & Worker
- [ ] Add `TWILIO_PHONE_NUMBER` to API & Worker

### FCM (for Push Notifications)
- [ ] Add `FCM_SERVER_KEY` to API & Worker

### Custom Domains
- [ ] Add custom domain to API service
- [ ] Add custom domain to Web service
- [ ] Update DNS records
- [ ] Update `CORS_ORIGINS` with custom domain

### Monitoring
- [ ] Set up log alerts (Railway Pro)
- [ ] Enable database backups (Railway Pro)
- [ ] Set up uptime monitoring (external service)

---

## Troubleshooting

### API won't start
- [ ] Check DATABASE_URL is correct
- [ ] Check JWT_SECRET is at least 32 chars
- [ ] View logs for Python errors

### Frontend can't connect
- [ ] Verify NEXT_PUBLIC_API_URL is correct
- [ ] Check CORS_ORIGINS includes frontend domain
- [ ] Check API service is running (green indicator)

### Worker not processing
- [ ] Check Worker logs for SQL errors
- [ ] Verify DATABASE_URL and REDIS_URL
- [ ] Check worker service is running

---

## Success! 🎉

Your EzMsg application should now be live:

- **Frontend**: `https://your-web-domain.up.railway.app`
- **API**: `https://your-api-domain.up.railway.app`
- **Protocol API**: Available at `/v1/protocol/*`

---

## Next Steps

1. Change default admin password
2. Import production protocol data
3. Test with real participants
4. Set up monitoring alerts
5. Configure Twilio for production SMS

---

**Need Help?**
- 📖 Full Guide: [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)
- 💬 Railway Discord: [discord.gg/railway](https://discord.gg/railway)
- 🐛 Report Issues: GitHub Issues
