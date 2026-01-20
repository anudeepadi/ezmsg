#!/usr/bin/env python3
"""
EzMsg Setup Verification Script
Tests database connections and verifies environment setup
"""

import asyncio
import os
import sys
from pathlib import Path

# Add api directory to path
sys.path.insert(0, str(Path(__file__).parent / "api"))


async def test_redis():
    """Test Redis connection"""
    try:
        import redis.asyncio as redis
        import ssl

        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            print("❌ REDIS_URL not found in environment")
            return False

        print(f"🔍 Testing Redis connection...")
        print(f"   URL: {redis_url.split('@')[1] if '@' in redis_url else redis_url}")

        # For rediss:// (TLS), the redis library handles SSL automatically
        # Just need to disable certificate verification for self-signed certs
        client = redis.from_url(
            redis_url,
            decode_responses=True,
            ssl_cert_reqs="none"  # Disable SSL certificate verification
        )

        # Test connection
        await client.ping()
        print("✅ Redis connection successful!")

        # Test basic operations
        await client.set("test_key", "test_value")
        value = await client.get("test_key")
        await client.delete("test_key")

        if value == "test_value":
            print("✅ Redis read/write operations work!")

        await client.close()
        return True

    except ImportError:
        print("❌ redis package not installed. Run: pip install redis")
        return False
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print(f"   This might be a network or SSL issue")
        print(f"   Verify your Redis URL and that the service is active")
        return False


async def test_postgres():
    """Test PostgreSQL connection"""
    try:
        import asyncpg

        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in environment")
            return False

        # Check if placeholder password still exists
        if 'YOUR_PASSWORD' in database_url:
            print("⚠️  DATABASE_URL contains placeholder password")
            print("   Please update .env.local with your actual Supabase password")
            print("\n📝 How to get your Supabase password:")
            print("   1. Go to https://supabase.com")
            print("   2. Open your 'exmsg-dev' project")
            print("   3. Click Settings → Database")
            print("   4. Scroll to 'Connection string' → Click 'URI' tab")
            print("   5. Copy the full connection string")
            print("   6. Replace DATABASE_URL in .env.local")
            print("   7. Change 'postgresql://' to 'postgresql+asyncpg://'")
            return False

        print(f"🔍 Testing PostgreSQL connection...")

        # Remove +asyncpg for asyncpg library
        clean_url = database_url.replace('+asyncpg', '')

        # Parse to hide password in output
        if '@' in clean_url:
            parts = clean_url.split('@')
            display_url = f"***@{parts[1]}"
        else:
            display_url = clean_url

        print(f"   URL: {display_url}")

        conn = await asyncpg.connect(clean_url)

        # Test connection
        version = await conn.fetchval('SELECT version()')
        print("✅ PostgreSQL connection successful!")
        print(f"   Version: {version.split()[0]} {version.split()[1]}")

        # Check if tables exist
        tables = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)

        if tables:
            print(f"✅ Found {len(tables)} existing tables")
        else:
            print("ℹ️  No tables found (database schema not initialized yet)")

        await conn.close()
        return True

    except ImportError:
        print("❌ asyncpg package not installed. Run: pip install asyncpg")
        return False
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False


async def main():
    """Run all verification tests"""
    print("=" * 60)
    print("🚀 EzMsg Setup Verification")
    print("=" * 60)
    print()

    # Check .env.local exists
    env_file = Path(__file__).parent / ".env.local"
    if not env_file.exists():
        print("❌ .env.local file not found!")
        print("   Please create it from .env.local.example")
        return

    print("✅ .env.local file found")
    print()

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv(env_file)

    # Test Redis
    print("=" * 60)
    print("Testing Redis Connection")
    print("=" * 60)
    redis_ok = await test_redis()
    print()

    # Test PostgreSQL
    print("=" * 60)
    print("Testing PostgreSQL Connection")
    print("=" * 60)
    postgres_ok = await test_postgres()
    print()

    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    if redis_ok and postgres_ok:
        print("✅ All connections successful!")
        print()
        print("📝 Next steps:")
        print("   1. Initialize database schema:")
        print("      cd api && source venv/bin/activate")
        print("      export $(cat ../.env.local | xargs)")
        print("      python scripts/init_database.py")
        print()
        print("   2. Import protocol data:")
        print("      python scripts/import_quittxt_v9_protocol.py")
        print("      python scripts/add_quittxt_v9_q8_q21.py")
        print()
        print("   3. Start API server:")
        print("      uvicorn app.main:app --reload --port 8000")

    elif redis_ok:
        print("✅ Redis connection works")
        print("⚠️  PostgreSQL needs configuration")
        print()
        print("📝 To fix PostgreSQL:")
        print("   Update DATABASE_URL in .env.local with your Supabase password")

    elif postgres_ok:
        print("✅ PostgreSQL connection works")
        print("⚠️  Redis needs configuration")

    else:
        print("⚠️  Both connections need configuration")
        print()
        print("📖 See QUICKSTART.md for detailed setup instructions")


if __name__ == "__main__":
    asyncio.run(main())
