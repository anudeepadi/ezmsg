#!/bin/bash

# =============================================================================
# EzMsg Local Database Setup with Free External Services
# =============================================================================
# This script helps you set up Supabase and Upstash for local development
# =============================================================================

set -e  # Exit on error

echo "🚀 EzMsg Local Database Setup"
echo "================================"
echo ""
echo "This script will help you set up free external databases for local testing:"
echo "• Supabase (PostgreSQL) - Free 500MB"
echo "• Upstash (Redis) - Free 10k commands/day"
echo ""

# Check if .env.local exists
if [ -f .env.local ]; then
    echo "⚠️  .env.local already exists!"
    read -p "Do you want to overwrite it? (y/n): " overwrite
    if [ "$overwrite" != "y" ]; then
        echo "Exiting. Please edit .env.local manually."
        exit 0
    fi
fi

# Create .env.local from template
if [ ! -f .env.local.example ]; then
    echo "❌ .env.local.example not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

cp .env.local.example .env.local
echo "✅ Created .env.local from template"
echo ""

# Get Supabase credentials
echo "📝 Step 1: Supabase PostgreSQL Setup"
echo "================================"
echo ""
echo "1. Go to https://supabase.com and create account"
echo "2. Create a new project"
echo "3. Wait for provisioning (2-3 minutes)"
echo "4. Go to Settings → Database → Connection string → URI"
echo ""
read -p "Enter your Supabase connection string (postgresql://...): " supabase_url

# Convert to asyncpg format if needed
if [[ $supabase_url == postgresql://* ]]; then
    supabase_url="${supabase_url/postgresql:\/\//postgresql+asyncpg://}"
fi

# Update .env.local with Supabase URL
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s|DATABASE_URL=.*|DATABASE_URL=$supabase_url|" .env.local
else
    # Linux
    sed -i "s|DATABASE_URL=.*|DATABASE_URL=$supabase_url|" .env.local
fi

echo "✅ Supabase connection string saved"
echo ""

# Get Upstash credentials
echo "📝 Step 2: Upstash Redis Setup"
echo "================================"
echo ""
echo "1. Go to https://upstash.com and create account"
echo "2. Create a new Redis database"
echo "3. Copy the connection string"
echo ""
read -p "Enter your Upstash Redis URL (redis://... or rediss://...): " redis_url

# Update .env.local with Redis URL
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s|REDIS_URL=.*|REDIS_URL=$redis_url|" .env.local
else
    # Linux
    sed -i "s|REDIS_URL=.*|REDIS_URL=$redis_url|" .env.local
fi

echo "✅ Upstash connection string saved"
echo ""

# Test connections
echo "🧪 Step 3: Testing Connections"
echo "================================"
echo ""

# Load environment variables
export $(cat .env.local | grep -v '^#' | xargs)

echo "Testing PostgreSQL connection..."
cd api
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing dependencies..."
pip install -q asyncpg python-dotenv

# Test PostgreSQL
python3 -c "
import asyncio
import os
import asyncpg

async def test():
    try:
        url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
        conn = await asyncpg.connect(url)
        version = await conn.fetchval('SELECT version()')
        print('✅ PostgreSQL connection successful!')
        print(f'   Version: {version.split()[0]} {version.split()[1]}')
        await conn.close()
        return True
    except Exception as e:
        print(f'❌ PostgreSQL connection failed: {e}')
        return False

success = asyncio.run(test())
exit(0 if success else 1)
" && pg_success=true || pg_success=false

echo ""

# Test Redis (we'll skip this for now as it requires redis-py)
echo "✅ Redis URL saved (manual testing recommended)"

cd ..

echo ""
echo "================================"
echo "✅ Setup Complete!"
echo "================================"
echo ""

if [ "$pg_success" = true ]; then
    echo "Your .env.local is configured and PostgreSQL connection works!"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Initialize database schema:"
    echo "   cd api"
    echo "   source venv/bin/activate"
    echo "   export \$(cat ../.env.local | xargs)"
    echo "   python -c \"
    echo "   import asyncio"
    echo "   from app.database.engine import engine"
    echo "   from app.models import Base"
    echo "   async def init(): await (await engine.begin()).__aenter__().run_sync(Base.metadata.create_all)"
    echo "   asyncio.run(init())"
    echo "   \""
    echo ""
    echo "2. Create admin user:"
    echo "   See SETUP_FREE_DATABASES.md for instructions"
    echo ""
    echo "3. Start API server:"
    echo "   uvicorn app.main:app --reload --port 8000"
    echo ""
    echo "4. Test:"
    echo "   curl http://localhost:8000/health"
    echo ""
    echo "📖 Full guide: SETUP_FREE_DATABASES.md"
else
    echo "⚠️  PostgreSQL connection test failed."
    echo "Please check your connection string and try again."
    echo ""
    echo "Edit .env.local manually if needed."
    echo ""
    echo "📖 See SETUP_FREE_DATABASES.md for detailed instructions"
fi

echo ""
