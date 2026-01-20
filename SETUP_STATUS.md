# 📊 EzMsg Setup Status

Last updated: 2026-01-20

---

## ✅ Completed Steps

1. **Project Structure** - ✅ All code and services implemented
2. **Documentation** - ✅ Deployment guides created (Railway, Quickstart, Database Setup)
3. **Protocol API** - ✅ External API with API key authentication implemented
4. **GitHub Repository** - ✅ Pushed to https://github.com/anudeepadi/silver-octo-rotary-phone
5. **Environment Template** - ✅ `.env.local` file created with configurations
6. **Verification Script** - ✅ `verify-setup.py` created to test connections

---

## ⏳ Pending Steps

### **1. Database Connection Strings**

#### **Supabase PostgreSQL** - ⚠️ Needs Password
- **Status**: Project created, credentials partially configured
- **Project**: `exmsg-dev` (nkxewmxszqtjaeveimou.supabase.co)
- **What's Missing**: Database password
- **Where to Get It**:
  1. Go to https://supabase.com
  2. Open your "exmsg-dev" project
  3. Click **Settings** → **Database**
  4. Scroll to **"Connection string"** → Click **"URI"** tab
  5. Copy the full connection string (it includes your password)
  6. Update `.env.local` line 20:
     ```bash
     # Change this:
     DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@db.nkxewmxszqtjaeveimou.supabase.co:5432/postgres

     # To your actual connection string (keep postgresql+asyncpg://):
     DATABASE_URL=postgresql+asyncpg://postgres.YOUR_REF:YOUR_ACTUAL_PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres
     ```

#### **Redis Labs** - ⚠️ SSL Connection Issue
- **Status**: Credentials provided, but SSL handshake failing
- **Connection**: `redis-16847.c278.us-east-1-4.ec2.cloud.redislabs.com:16847`
- **Error**: `[SSL] record layer failure`
- **Possible Causes**:
  - The rediss:// URL might be incorrect
  - The password might have changed
  - The Redis Labs service might be inactive
  - Port 16847 might not support TLS

- **How to Verify/Fix**:
  1. Log into https://cloud.redislabs.com (or https://app.redislabs.com)
  2. Click on your Redis database
  3. Check if the database is **"Active"**
  4. Copy the connection string from the dashboard (look for "Public endpoint" or "Redis connection string")
  5. The format should be one of:
     - `redis://default:PASSWORD@host:port` (no TLS)
     - `rediss://default:PASSWORD@host:port` (with TLS)
  6. Update `.env.local` line 27 with the correct URL

---

## 🔧 How to Test Your Configuration

### **Run the Verification Script**

```bash
cd /Users/vuc229/Documents/Development/Active-Projects/infrastructure/ezmsg-new
source api/venv/bin/activate
python verify-setup.py
```

This will test both PostgreSQL and Redis connections and tell you exactly what needs to be fixed.

---

## 📝 Once Both Connections Work

After both database connections are verified:

### **1. Initialize Database Schema**

```bash
cd api
source venv/bin/activate
export $(cat ../.env.local | xargs)

# Create all tables
python -c "
import asyncio
from app.database.engine import engine
from app.models import Base

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('✅ Database schema created!')

asyncio.run(init_db())
"
```

### **2. Create Admin User**

```bash
python -c "
import asyncio
from app.database.session import get_db_context
from app.models.user import User
from app.security.auth import get_password_hash
from sqlalchemy import select

async def create_admin():
    async with get_db_context() as db:
        result = await db.execute(select(User).where(User.email == 'admin@example.com'))
        if result.scalar_one_or_none():
            print('ℹ️  Admin already exists')
            return
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

### **3. Import Protocol Data**

```bash
# Import QuitTxt V9 base protocol (132 nodes)
python scripts/import_quittxt_v9_protocol.py

# Import extended days (Q8-Q21+)
python scripts/add_quittxt_v9_q8_q21.py
```

### **4. Start API Server**

```bash
export $(cat ../.env.local | xargs)
uvicorn app.main:app --reload --port 8000
```

### **5. Test API**

```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'

# Protocol API test
curl -X POST http://localhost:8000/v1/protocol/start \
  -H "Content-Type: application/json" \
  -H "X-API-Key: iquit0-test-key-12345" \
  -d '{
    "project_id": 7,
    "language": "en",
    "initial_response": "iquit0"
  }'
```

### **6. Start Frontend**

```bash
cd ../web
export NEXT_PUBLIC_API_URL=http://localhost:8000
npm install  # First time only
npm run dev
```

Visit: http://localhost:3000

---

## 🚀 After Local Testing Succeeds

Once everything works locally with Supabase and Redis Labs:

1. **Keep the same database URLs** for Railway deployment
2. No need to create new Railway PostgreSQL/Redis services
3. Just deploy API, Worker, and Web services to Railway
4. Use the same `.env.local` values as Railway environment variables

This approach means:
- ✅ No data migration needed
- ✅ Same databases for local dev and Railway
- ✅ Easier debugging (same data everywhere)
- ✅ Lower Railway costs (no managed database charges)

---

## 🆘 Need Help?

- **Detailed Setup**: See `SETUP_FREE_DATABASES.md`
- **Quick Start**: See `QUICKSTART.md`
- **Railway Deploy**: See `RAILWAY_DEPLOYMENT.md`
- **Next Step**: See `NEXT_STEP.md`

---

## 📞 Current Blockers

1. **PostgreSQL**: Waiting for Supabase database password from Settings → Database → Connection string → URI
2. **Redis**: SSL connection failing - need to verify Redis Labs dashboard shows correct connection string and service is active
