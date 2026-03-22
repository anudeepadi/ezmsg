# Secrets Rotation Checklist

This document lists all secrets that were previously exposed in documentation and need to be rotated for security.

## Immediate Action Required

The following secrets were found in documentation files and have been redacted. You should rotate them as soon as possible.

### 1. Database Credentials

**What was exposed:**
- Supabase PostgreSQL connection string with password
- Database: `postgres`
- Host: `aws-1-us-east-1.pooler.supabase.com:5432`
- Project ID: `nkxewmxszqtjaeveimou`
- Password: `Factorysmokeloud2$` (URL-encoded as `Factorysmokeloud2%24`)

**Action required:**
1. Go to Supabase dashboard (https://supabase.com)
2. Navigate to your project: `exmsg-dev`
3. Go to Settings → Database → Reset database password
4. Update the new password in all deployment environments:
   - Railway environment variables
   - Local `.env.local` files (if any exist)
   - Any CI/CD systems

### 2. Redis Credentials

**What was exposed:**
- Redis Labs connection string with password
- Host: `redis-16847.c278.us-east-1-4.ec2.cloud.redislabs.com:16847`
- Password: `bRjLQBRYXcs5Pt1H2PNgZA7HFFDqIhaZ`

**Action required:**
1. Go to Redis Labs dashboard (https://app.redislabs.com)
2. Navigate to your database
3. Regenerate the password or recreate the database
4. Update the new connection string in all deployment environments

### 3. Supabase API Keys

**What was exposed:**
- Supabase Project URL: `https://nkxewmxszqtjaeveimou.supabase.co`
- Supabase Anon Key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (full JWT)
- Supabase Service Role Key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (full JWT)

**Action required:**
1. Go to Supabase dashboard
2. Navigate to Settings → API
3. Note: Anon key is typically safe to expose, but service role key is sensitive
4. Consider rotating the service role key if it was publicly accessible
5. Update in all deployment environments if rotated

### 4. Protocol API Key (Hardcoded)

**What was exposed:**
- API Key: `iquit0-test-key-12345` (development/test key)

**Action required:**
1. Check if this key is still hardcoded in `api/app/routers/protocol_api.py`
2. Replace hardcoded value with environment variable:
   ```python
   import os
   API_KEY = os.getenv("PROTOCOL_API_KEY", "iquit0-test-key-12345")
   ```
3. Generate a new secure key:
   ```bash
   openssl rand -hex 32
   ```
4. Set `PROTOCOL_API_KEY` environment variable in Railway and local environments
5. Update any external systems that use this API key

### 5. JWT Secret (Development Key)

**What was exposed:**
- JWT Secret: `local-dev-secret-key-for-ezmsg-testing-replace-in-production-min-32-chars`

**Action required:**
1. This appears to be a development key, but verify it's not used in production
2. Ensure production environments use a secure, randomly generated secret:
   ```bash
   openssl rand -base64 48
   ```
3. Set `JWT_SECRET` environment variable in Railway

## Files That Were Updated

The following files had secrets redacted:
- `DEPLOYMENT_READY.md`
- `DEPLOY_TO_RAILWAY.md`
- `RAILWAY_QUICK_DEPLOY.md`

## Verification Steps

After rotating secrets:

1. Test database connection:
   ```bash
   python verify-setup.py
   ```

2. Test API health:
   ```bash
   curl https://your-api-url.railway.app/health
   ```

3. Test protocol API with new key:
   ```bash
   curl -X POST https://your-api-url.railway.app/v1/protocol/start \
     -H "X-API-Key: YOUR_NEW_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"project_id": 7, "language": "en", "initial_response": "iquit0"}'
   ```

4. Test admin login with updated JWT secret

## Best Practices Going Forward

1. Never commit real secrets to git repositories
2. Always use environment variables for sensitive data
3. Use `.env.example` files with placeholder values only
4. Add actual `.env` files to `.gitignore`
5. Rotate secrets regularly (every 90 days minimum)
6. Use different secrets for development, staging, and production
7. Store secrets in a secure password manager or secrets management service
8. Enable Railway's "Secret" type for sensitive environment variables

## Notes

- The Supabase anon key is generally safe to expose in client-side code, but the service role key must remain secret
- The Protocol API key should be treated as a sensitive credential
- Redis is optional; the system can function without it (used only for caching)
