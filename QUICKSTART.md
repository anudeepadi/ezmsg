# 🚀 EzMsg Quick Start - Test with Free External Databases

Get EzMsg running locally in **15 minutes** using free Supabase (PostgreSQL) and Upstash (Redis).

---

## 📋 Prerequisites

- Python 3.12+
- Node.js 20+
- Git

---

## ⚡ Quick Setup (5 steps)

### **Step 1: Get Free Database Accounts (5 min)**

#### **Supabase (PostgreSQL)**
1. Go to [supabase.com](https://supabase.com) → Sign up (free, no credit card)
2. Click **"New Project"**
3. Set name: `ezmsg-dev`, choose password, select region
4. Wait 2-3 min for provisioning
5. Go to **Settings** → **Database** → **Connection string** → **URI**
6. Copy the connection string (looks like: `postgresql://postgres:PASSWORD@db.xxx.supabase.co:5432/postgres`)

#### **Upstash (Redis)**
1. Go to [upstash.com](https://upstash.com) → Sign up (free, no credit card)
2. Click **"Create Database"**
3. Set name: `ezmsg-redis`, choose region, enable TLS
4. Copy the connection string (looks like: `rediss://default:PASSWORD@xxx.upstash.io:6379`)

---

### **Step 2: Configure Environment (1 min)**

```bash
# Copy template
cp .env.local.example .env.local

# Edit .env.local and replace:
# - DATABASE_URL with your Supabase connection (change postgresql:// to postgresql+asyncpg://)
# - REDIS_URL with your Upstash connection
```

**Example `.env.local`:**
```bash
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@db.xxx.supabase.co:5432/postgres
REDIS_URL=rediss://default:YOUR_PASSWORD@xxx.upstash.io:6379
JWT_SECRET=local-dev-secret-key-at-least-32-characters-long
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=["http://localhost:3000"]
SIMULATION_MODE=true
DEBUG=true
ENVIRONMENT=development
```

---

### **Step 3: Initialize Database (3 min)**

```bash
# Setup Python environment
cd api
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Load environment variables
export $(cat ../.env.local | xargs)

# Create database schema
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

# Create admin user
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
            print('Admin already exists')
            return
        admin = User(
            email='admin@example.com',
            full_name='Admin User',
            role='admin',
            hashed_password=get_password_hash('admin123')
        )
        db.add(admin)
        await db.commit()
        print('✅ Admin user created: admin@example.com / admin123')

asyncio.run(create_admin())
"

# Import QuitTxt V9 protocol
python scripts/import_quittxt_v9_protocol.py

# Import extended days (Q8-Q21+)
python scripts/add_quittxt_v9_q8_q21.py
```

---

### **Step 4: Start API Server (1 min)**

```bash
# Make sure you're in api/ with venv activated
export $(cat ../.env.local | xargs)
uvicorn app.main:app --reload --port 8000
```

You should see:
```
Starting EzMsg API...
Environment: development
Simulation mode: True
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### **Step 5: Start Frontend (1 min)**

Open a new terminal:

```bash
cd web
npm install  # First time only
export NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Visit: **http://localhost:3000**

Login with:
- **Email**: `admin@example.com`
- **Password**: `admin123`

---

## ✅ Verify Everything Works

### **Test API:**
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","app":"EzMsg API","environment":"development"}
```

### **Test Protocol API:**
```bash
curl -X POST http://localhost:8000/v1/protocol/start \
  -H "Content-Type: application/json" \
  -H "X-API-Key: iquit0-test-key-12345" \
  -d '{
    "project_id": 7,
    "language": "en",
    "initial_response": "iquit0"
  }'
```

Should return session with message text.

### **Check Supabase:**
1. Go to Supabase dashboard → **Table Editor**
2. You should see all tables with data
3. Check `projects` table → Should have "QuitTxt V9 UTSA Study"
4. Check `messaging_nodes` → Should have 132 nodes

---

## 🎯 What You Can Do Now

1. ✅ **Test Protocol Flow** - Use Protocol API via Postman
2. ✅ **Explore Admin UI** - Manage projects, participants, templates
3. ✅ **Run Protocol Simulator** - Test message sequences
4. ✅ **View Analytics** - See protocol statistics
5. ✅ **Test All Features** - Everything works with external DBs!

---

## 🚂 Deploy to Railway (After Testing)

Once everything works locally:

```bash
# Your databases are already set up!
# Just use the same connection strings in Railway:

Railway Environment Variables:
- DATABASE_URL = (same Supabase URL)
- REDIS_URL = (same Upstash URL)
- JWT_SECRET = (generate new one: openssl rand -base64 48)
- CORS_ORIGINS = ["https://your-railway-web-domain.up.railway.app"]
- SIMULATION_MODE = false (for production)
```

See `RAILWAY_DEPLOYMENT.md` for full Railway deployment guide.

---

## 🐛 Troubleshooting

### **"Connection refused" for PostgreSQL**
- Check DATABASE_URL has correct password
- Make sure it starts with `postgresql+asyncpg://`
- Test connection in Supabase SQL Editor

### **"Redis connection error"**
- Make sure REDIS_URL uses `rediss://` (double s for TLS)
- Check password is correct
- Verify Upstash database is "Active"

### **"Admin user not created"**
- Make sure database schema was created first
- Check for errors in the Python output
- Try the command again

### **"Import script failed"**
- Make sure you're in `api/` directory
- Activate venv: `source venv/bin/activate`
- Load env: `export $(cat ../.env.local | xargs)`
- Check database is accessible

---

## 📚 More Documentation

- **Setup Guide**: `SETUP_FREE_DATABASES.md` - Detailed setup instructions
- **Railway Deploy**: `RAILWAY_DEPLOYMENT.md` - Deploy to production
- **Railway Checklist**: `RAILWAY_CHECKLIST.md` - Quick deployment checklist
- **Main README**: `README.md` - Full documentation

---

## 💰 Cost

**$0/month** - Both Supabase and Upstash have generous free tiers:
- **Supabase Free**: 500MB storage, unlimited API requests
- **Upstash Free**: 10,000 commands/day, 256MB memory

Perfect for development and testing!

---

## 🎉 Success!

You now have EzMsg running locally with cloud databases. Everything is ready to test before deploying to Railway!

**Need help?** Check `SETUP_FREE_DATABASES.md` for detailed troubleshooting.
