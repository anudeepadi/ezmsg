Next Steps: Complete Database Configuration

You're almost there! Just need to verify and complete two database connection strings.

---

What You Need to Do

### **Step 1: Get Your Supabase Connection String**

1. Open your browser and go to: **https://supabase.com**
2. Sign in to your account
3. Click on your **"exmsg-dev"** project (or whichever project you created)
4. In the left sidebar, click **"Settings"** (⚙️ gear icon)
5. In the Configuration section, click **"Database"**
6. Scroll down to the **"Connection string"** section
7. Click the **"URI"** tab
8. Click **"Copy"** to copy the connection string

It will look like:
```
postgresql://postgres.nkxewmxszqtjaeveimou:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

**Important**: Make sure you see your actual password in the string (not `[YOUR-PASSWORD]`)

---

### **Step 2: Update .env.local**

1. Open `.env.local` in your editor
2. Find the line that says:
   ```bash
   DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@db.nkxewmxszqtjaeveimou.supabase.co:5432/postgres
   ```

3. Replace the entire line with your Supabase connection string
4. **Important**: Change `postgresql://` to `postgresql+asyncpg://` at the beginning

**Example:**

If Supabase gives you:
```
postgresql://postgres.nkxewmxszqtjaeveimou:abc123xyz@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

Change it to:
```
postgresql+asyncpg://postgres.nkxewmxszqtjaeveimou:abc123xyz@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

5. Save the file

---

### **Step 2b: Verify Redis Connection (Optional)**

The Redis connection is showing an SSL error. To verify it's correct:

1. Log into **https://cloud.redislabs.com** (or https://app.redislabs.com)
2. Click on your Redis database
3. Make sure the database status is **"Active"** (green indicator)
4. Look for the connection string in the dashboard
5. It should show something like:
   - **Public endpoint**: `redis-xxxxx.c278.us-east-1-4.ec2.cloud.redislabs.com:16847`
   - **Password**: `<your-redis-password>`

6. The connection URL in `.env.local` should be:
   ```bash
   # With TLS (recommended):
   REDIS_URL=rediss://default:PASSWORD@HOST:PORT

   # Or without TLS if rediss:// doesn't work:
   REDIS_URL=redis://default:PASSWORD@HOST:PORT
   ```

7. If you see a different format or password in your dashboard, update `.env.local` line 27

---

### **Step 3: Verify Connections**

Run the verification script:

```bash
cd /Users/vuc229/Documents/Development/Active-Projects/infrastructure/ezmsg-new

# Install dependencies if needed
cd api
source venv/bin/activate
pip install python-dotenv redis asyncpg

# Run verification
cd ..
python verify-setup.py
```

You should see:
```
✅ Redis connection successful!
✅ PostgreSQL connection successful!
```

---

### **Step 4: Initialize Database**

Once both connections work:

```bash
cd api
source venv/bin/activate
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

# Import protocol data
python scripts/import_quittxt_v9_protocol.py
python scripts/add_quittxt_v9_q8_q21.py
```

---

### **Step 5: Start the API Server**

```bash
cd api
source venv/bin/activate
export $(cat ../.env.local | xargs)
uvicorn app.main:app --reload --port 8000
```

Test it:
```bash
curl http://localhost:8000/health
```

---

That's It!

Once you complete these steps, your EzMsg system will be running with cloud databases!

**What's Configured:**
- ✅ Redis Labs (cloud Redis) - fully configured
- ⏳ Supabase (cloud PostgreSQL) - needs password
- ✅ JWT authentication settings
- ✅ CORS for localhost:3000
- ✅ Simulation mode enabled

**What's Next After This:**
- Test locally with cloud databases
- Run Protocol API tests via Postman
- Deploy to Railway with the same database URLs (no migration needed!)

---

� More Help

- **Quick Start**: See `QUICKSTART.md`
- **Detailed Setup**: See `SETUP_FREE_DATABASES.md`
- **Railway Deploy**: See `RAILWAY_DEPLOYMENT.md`
