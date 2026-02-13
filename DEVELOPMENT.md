# EzMsg — Development Guide

## Prerequisites

- Python 3.12+
- Node.js 20+ (for frontend)
- Docker (optional, for containerized setup)

## Option 1: Docker (Fastest)

```bash
cd docker
docker-compose up -d
```

This starts PostgreSQL, Redis, API, Worker, and Web. Access:
- **API**: http://localhost:8000 (docs at `/docs`)
- **Frontend**: http://localhost:3000

Admin credentials are generated on first startup and printed to the API container logs:
```bash
docker logs ezmsg-api 2>&1 | grep "admin"
```

## Option 2: Free Cloud Databases + Local Code

Use free tiers of Supabase (PostgreSQL) and Upstash (Redis) — no Docker needed, $0/month.

### Step 1: Create Free Database Accounts

**Supabase (PostgreSQL):**
1. Sign up at [supabase.com](https://supabase.com) (free, no credit card)
2. Create a new project (name: `ezmsg-dev`, choose a password, pick a region)
3. Wait 2-3 minutes for provisioning
4. Go to **Settings > Database > Connection string > URI**
5. Copy the URI and change `postgresql://` to `postgresql+asyncpg://`

**Upstash (Redis):**
1. Sign up at [upstash.com](https://upstash.com) (free, no credit card)
2. Create a Redis database (name: `ezmsg-redis`, enable TLS)
3. Copy the connection string (starts with `rediss://` — note the double-s for TLS)

### Step 2: Configure Environment

```bash
cp .env.local.example .env.local
```

Edit `.env.local` and fill in:
- `DATABASE_URL` — your Supabase connection string (with `postgresql+asyncpg://`)
- `REDIS_URL` — your Upstash connection string

All other settings have sensible defaults for development.

### Step 3: Start the API

```bash
cd api
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -e .

# Load env vars and start
export $(grep -v '^#' ../.env.local | xargs)
uvicorn app.main:app --reload --port 8000
```

On first startup, the API will:
1. Create all database tables
2. Create an admin user (credentials printed to console)

### Step 4: Start the Frontend (Optional)

```bash
cd web
npm install
npm run dev
```

Frontend runs at http://localhost:3000 and proxies API requests to port 8000.

### Step 5: Start the Worker (Optional)

```bash
cd worker
python -m venv venv
source venv/bin/activate
pip install -e .

export $(grep -v '^#' ../.env.local | xargs)
python -m app.main
```

## Importing Protocol Data

After the API is running, import the QuitTxt V9 protocol:

```bash
cd api
python scripts/import_quittxt_v9_protocol.py
```

This creates 63 messaging nodes, 61 templates (EN/ES), 12 variables, and 14 timing elements.

## Testing

### Run Unit Tests

```bash
cd api
pip install -e ".[dev]"
pytest tests/ -v
```

### Test Protocol Flow (HTTP)

```bash
# Start a session
curl -X POST http://localhost:8000/v1/protocol/start \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $PROTOCOL_API_KEY" \
  -d '{"project_id": 7, "language": "en", "initial_response": "iquit0"}'

# Respond to continue
curl -X POST http://localhost:8000/v1/protocol/respond \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $PROTOCOL_API_KEY" \
  -d '{"session_id": "YOUR_SESSION_ID", "response": "1"}'
```

### Postman Collection

Import `EzMsg_Protocol_API.postman_collection.json` into Postman for a pre-built test suite covering the full protocol flow.

### Test Scripts

| Script | Purpose |
|--------|---------|
| `test_protocol_flow.py` | Direct engine testing (6 scenarios) |
| `test_protocol_multiday.py` | HTTP API testing with timing analysis |
| `api/test_protocol_api_flow.py` | Mobile integration testing (EN, ES, immediate quit) |
| `verify-setup.py` | Infrastructure verification (Redis, Postgres, schema) |

## Database Migrations (Alembic)

Alembic is configured for schema migrations:

```bash
cd api

# After making model changes, generate a migration:
alembic revision --autogenerate -m "describe your changes"

# Apply migrations:
alembic upgrade head

# On a fresh database (after init_db.py creates tables):
alembic stamp 001    # Mark baseline as applied
```

## Code Quality

```bash
cd api

# Lint
ruff check app/

# Format
ruff format app/

# Type check
mypy app/ --ignore-missing-imports
```

## Environment Variables Reference

See `.env.local.example` for all available settings. Key variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | local postgres | PostgreSQL connection (asyncpg) |
| `REDIS_URL` | Yes | localhost:6379 | Redis connection |
| `JWT_SECRET` | Prod only | auto-generated | JWT signing key (32+ chars) |
| `PROTOCOL_API_KEY` | For API | none | Protocol endpoint auth key |
| `ADMIN_EMAIL` | No | admin@ezmsg.local | Seed admin email |
| `ADMIN_PASSWORD` | No | auto-generated | Seed admin password |
| `ENVIRONMENT` | No | development | development / production |
| `SIMULATION_MODE` | No | true | Skip real SMS/FCM delivery |
| `DEBUG` | No | false | Enable verbose logging + /docs |
