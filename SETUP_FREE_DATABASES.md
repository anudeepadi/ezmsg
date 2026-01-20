# 🆓 Setup Free External Databases for Local Testing

Before deploying to Railway, let's test with free external databases to ensure everything works.

---

## 📋 What We'll Set Up

1. **Supabase** - Free PostgreSQL database (500MB storage, unlimited API requests)
2. **Upstash** - Free Redis database (10,000 commands/day)

Both services have generous free tiers perfect for testing and development.

---

## 🐘 Step 1: Set Up Supabase (PostgreSQL)

### **1.1 Create Supabase Account**

1. Go to [supabase.com](https://supabase.com)
2. Click **"Start your project"**
3. Sign up with GitHub (recommended) or email
4. Verify your email if needed

### **1.2 Create New Project**

1. Click **"New Project"**
2. Fill in details:
   - **Name**: `ezmsg-dev` or any name you like
   - **Database Password**: Choose a strong password (save it!)
   - **Region**: Choose closest to you (e.g., `US West`)
   - **Pricing Plan**: Free (automatic)
3. Click **"Create new project"**
4. Wait 2-3 minutes for provisioning

### **1.3 Get Connection String**

1. In your project dashboard, click **"Settings"** (gear icon in sidebar)
2. Go to **"Database"** section
3. Scroll to **"Connection string"**
4. Select **"URI"** tab
5. Copy the connection string - it looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres
   ```
6. Replace `[YOUR-PASSWORD]` with your actual database password

### **1.4 Enable Extensions (Optional but Recommended)**

1. Go to **"Database"** → **"Extensions"**
2. Enable these extensions:
   - `uuid-ossp` (for UUID generation)
   - `pg_stat_statements` (for performance monitoring)

### **1.5 Configure Connection for Python**

Supabase uses connection pooling. For Python/SQLAlchemy, use this format:

```
postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres
```

**Save this connection string!** We'll use it in `.env.local`

---

## 🔴 Step 2: Set Up Upstash (Redis)

### **2.1 Create Upstash Account**

1. Go to [upstash.com](https://upstash.com)
2. Click **"Start for Free"**
3. Sign up with GitHub, Google, or email
4. Verify your email if needed

### **2.2 Create Redis Database**

1. In the dashboard, click **"Create Database"**
2. Fill in details:
   - **Name**: `ezmsg-dev-redis`
   - **Type**: Select **"Regional"**
   - **Region**: Choose closest to you
   - **TLS**: Enable (recommended)
3. Click **"Create"**
4. Database is created instantly!

### **2.3 Get Connection String**

1. Click on your newly created database
2. Scroll down to **"REST API"** section
3. You'll see connection details:
   - **Endpoint**: `https://xxx.upstash.io`
   - **Password**: Your Redis password

4. For Python (redis-py), use this format:
   ```
   redis://default:[YOUR-PASSWORD]@xxx.upstash.io:6379
   ```

   Or with TLS (recommended):
   ```
   rediss://default:[YOUR-PASSWORD]@xxx.upstash.io:6379
   ```

**Note**: Upstash Redis uses TLS by default. The `rediss://` protocol (with double 's') enables TLS.

**Save this connection string!** We'll use it in `.env.local`

---

## 🔧 Step 3: Configure Local Environment

### **3.1 Create `.env.local` File**

Create this file in the root of your project:

```bash
cd /Users/vuc229/Documents/Development/Active-Projects/infrastructure/ezmsg-new
```

Create `.env.local`:

```bash
# =============================================================================
# Local Development with External Databases
# =============================================================================

# Supabase PostgreSQL
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_SUPABASE_PASSWORD@db.xxx.supabase.co:5432/postgres

# Upstash Redis (with TLS)
REDIS_URL=rediss://default:YOUR_UPSTASH_PASSWORD@xxx.upstash.io:6379

# JWT Authentication
JWT_SECRET=local-dev-secret-key-at-least-32-characters-long-for-testing
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS - Allow localhost
CORS_ORIGINS=["http://localhost:3000"]

# Application Settings
SIMULATION_MODE=true
DEBUG=true
ENVIRONMENT=development

# Optional: Twilio (leave empty for testing)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# Optional: FCM (leave empty for testing)
FCM_SERVER_KEY=
```

### **3.2 Update `api/.env` (if exists)**

If you have an `api/.env` file, update it with the same values, or just reference the root `.env.local`:

```bash
# In api/ directory
ln -s ../.env.local .env
```

### **3.3 Update `worker/.env` (if exists)**

Same for worker:

```bash
# In worker/ directory
ln -s ../.env.local .env
```

---

## 🗄️ Step 4: Initialize Supabase Database

### **4.1 Test Connection**

First, let's verify we can connect:

```bash
# Activate virtual environment
cd api
source venv/bin/activate

# Test connection
python -c "
import asyncio
import os
from dotenv import load_dotenv
load_dotenv('../.env.local')
import asyncpg

async def test():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL').replace('+asyncpg', ''))
    version = await conn.fetchval('SELECT version()')
    print('✅ Connected to PostgreSQL!')
    print(f'Version: {version}')
    await conn.close()

asyncio.run(test())
"
```

### **4.2 Run Database Migrations**

Now let's create the schema:

```bash
# Make sure you're in api/ directory with venv activated
cd api
source venv/bin/activate

# Load environment variables
export $(cat ../.env.local | xargs)

# Option 1: Using Alembic (if set up)
alembic upgrade head

# Option 2: Direct schema creation (if no Alembic)
python -c "
import asyncio
import os
from dotenv import load_dotenv
load_dotenv('../.env.local')

from app.database.engine import engine
from app.models import Base

async def init_db():
    async with engine.begin() as conn:
        print('Creating database schema...')
        await conn.run_sync(Base.metadata.create_all)
        print('✅ Database schema created!')

asyncio.run(init_db())
"
```

### **4.3 Create Admin User**

```bash
python -c "
import asyncio
from dotenv import load_dotenv
load_dotenv('../.env.local')

from app.database.session import get_db_context
from app.models.user import User
from app.security.auth import get_password_hash

async def create_admin():
    async with get_db_context() as db:
        # Check if admin exists
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == 'admin@example.com'))
        if result.scalar_one_or_none():
            print('Admin user already exists')
            return

        # Create admin
        admin = User(
            email='admin@example.com',
            full_name='Admin User',
            role='admin',
            hashed_password=get_password_hash('admin123')
        )
        db.add(admin)
        await db.commit()
        print('✅ Admin user created!')
        print('   Email: admin@example.com')
        print('   Password: admin123')

asyncio.run(create_admin())
"
```

---

## 🧪 Step 5: Test Locally with External Databases

### **5.1 Start API Service**

```bash
# In api/ directory with venv activated
export $(cat ../.env.local | xargs)
uvicorn app.main:app --reload --port 8000
```

You should see:
```
Starting EzMsg API...
Environment: development
Simulation mode: True
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### **5.2 Test Health Endpoint**

Open another terminal:

```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "app": "EzMsg API",
  "environment": "development"
}
```

### **5.3 Test Login**

```bash
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'
```

Should return user info and session cookie.

### **5.4 Test Protocol API**

```bash
curl -X POST http://localhost:8000/v1/protocol/start \
  -H "Content-Type: application/json" \
  -H "X-API-Key: iquit0-test-key-12345" \
  -d '{"project_id": 7, "language": "en", "initial_response": "iquit0"}'
```

**Note**: This will fail until you import protocol data (step 6).

### **5.5 Start Worker Service (Optional)**

In another terminal:

```bash
cd worker
source venv/bin/activate
export $(cat ../.env.local | xargs)
python -m app.main
```

### **5.6 Start Frontend**

In another terminal:

```bash
cd web
export NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Visit: http://localhost:3000

---

## 📊 Step 6: Import Protocol Data

### **6.1 Import QuitTxt V9 Protocol**

```bash
cd api
source venv/bin/activate
export $(cat ../.env.local | xargs)

# Run the import script
python scripts/import_quittxt_v9_protocol.py
```

### **6.2 Import Extended Days (Q8-Q21+)**

```bash
python scripts/add_quittxt_v9_q8_q21.py
```

### **6.3 Verify in Supabase**

1. Go to Supabase dashboard
2. Click **"Table Editor"**
3. You should see tables:
   - `users`
   - `projects`
   - `messaging_nodes`
   - `message_templates`
   - etc.

4. Click on `projects` - you should see "QuitTxt V9 UTSA Study"

---

## ✅ Step 7: Verify Everything Works

### **Checklist:**

- [ ] **Supabase Connection**: `psql` connection works
- [ ] **Upstash Connection**: Redis connection works
- [ ] **Database Schema**: Tables created in Supabase
- [ ] **Admin User**: Can login at http://localhost:3000
- [ ] **Protocol Data**: QuitTxt V9 imported (132 nodes)
- [ ] **API Health**: http://localhost:8000/health returns healthy
- [ ] **Frontend**: http://localhost:3000 loads login page
- [ ] **Protocol API**: Can start session and receive messages

---

## 🔍 Troubleshooting

### **"asyncpg.exceptions.InvalidPasswordError"**

- Check your Supabase password is correct in `.env.local`
- Make sure you replaced `[YOUR-PASSWORD]` with actual password
- Password shouldn't have special characters that need URL encoding

### **"Redis connection refused"**

- Make sure you're using `rediss://` (with double 's') for TLS
- Check Upstash password is correct
- Verify your Upstash database is in "Active" state

### **"No module named 'dotenv'"**

```bash
pip install python-dotenv
```

### **"Database migration failed"**

- Check DATABASE_URL is correct in `.env.local`
- Try connecting to Supabase using their SQL Editor to verify credentials
- Make sure PostgreSQL version is compatible (Supabase uses PG 15)

### **"Worker SQLAlchemy error"**

This is a known issue. The worker has SQL syntax that needs fixing. For now, just test without the worker.

---

## 📊 Database Dashboard Access

### **Supabase Dashboard:**
- URL: https://app.supabase.com
- Features:
  - Table Editor (view/edit data)
  - SQL Editor (run queries)
  - API Docs (auto-generated)
  - Logs & Monitoring

### **Upstash Dashboard:**
- URL: https://console.upstash.com
- Features:
  - CLI (run Redis commands in browser)
  - Metrics (requests, latency)
  - Logs

---

## 💰 Free Tier Limits

### **Supabase Free Tier:**
- 500 MB database space
- Unlimited API requests
- Up to 50,000 monthly active users
- 5 GB bandwidth
- **No credit card required!**

### **Upstash Free Tier:**
- 10,000 commands per day
- 256 MB max memory
- TLS support
- Global replication
- **No credit card required!**

---

## 🚀 Next Steps

After everything works locally:

1. ✅ Verify all features work with external databases
2. ✅ Test Protocol API thoroughly
3. ✅ Import all protocol data
4. ✅ Test frontend flows
5. 🚂 Deploy to Railway with confidence!

---

## 🔄 Using These Databases with Railway

**Good news!** You can use these same external databases with Railway:

1. In Railway, skip adding PostgreSQL/Redis services
2. Just set `DATABASE_URL` and `REDIS_URL` to your Supabase/Upstash URLs
3. Same `.env` variables work!

**Benefit**: You keep your data when switching between local and Railway.

---

**Ready to test? Let's go! 🎉**
