# EzMsg — Messaging Protocol Management System

A full-stack platform for managing messaging protocols in health interventions, built for the QuitTxt Research Study.

## Repository Structure

```
ezmsg/
├── backend/           # FastAPI backend (Python 3.12)
│   ├── app/           #   Application code
│   ├── tests/         #   Backend test suite
│   └── worker/        #   Background message scheduler
├── frontend/          # Next.js 14 frontend (React 18)
│   ├── app/           #   Pages and routes
│   ├── components/    #   UI components
│   └── lib/           #   Utilities
├── docs/              # Deployment guides and reference docs
├── scripts/           # Setup, test, and deployment scripts
├── docker-compose.yml # Local development (db + backend + frontend)
└── docker-compose.prod.yml
```

## Quick Start (Docker)

The fastest way to run the full stack locally:

```bash
# 1. Clone and enter the repo
git clone <repo-url> && cd ezmsg

# 2. Copy environment template
cp .env.example .env.local

# 3. Start everything (Postgres, Redis, Backend, Frontend)
docker compose up

# 4. Open the app
#    Frontend:  http://localhost:3000
#    API docs:  http://localhost:8000/docs
```

Default credentials: `admin@ezmsg.dev` / `admin123`

## Local Development (without Docker)

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16 (or use Docker for just the database)
- Redis 7 (or use Docker for just Redis)

### Database only via Docker

```bash
# Start only Postgres and Redis
docker compose up postgres redis
```

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend proxies `/api/*` requests to `http://localhost:8000/v1` via `next.config.js` rewrites.

### Worker (background scheduler)

```bash
cd backend/worker
python -m venv venv && source venv/bin/activate
pip install -e .
SIMULATION_MODE=true python -m app.main
```

## Features

- **Admin Dashboard** — project management, participant enrollment, message template editor (EN/ES), node graph editor, analytics
- **Messaging Engine** — scheduled delivery, FCM push notifications, variable substitution, quick replies, keyword handling, exponential backoff retries
- **Protocol API** — REST endpoints for external chatbot / mobile app integration

## API Overview

| Group | Path | Purpose |
|-------|------|---------|
| Auth | `/v1/auth/*` | Login, logout, refresh, current user |
| Admin | `/v1/admin/*` | Projects, participants, templates, nodes, variables, analytics |
| Scheduler | `/v1/scheduler/*` | Queue health, requeue, abort |
| Webhooks | `/v1/webhooks/*` | Twilio SMS, FCM token refresh, quick replies |
| Protocol | `/v1/protocol/*` | External integration (API-key auth) |

## Environment Variables

See `.env.example` for all available configuration. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://ezmsg:ezmsg_dev@localhost:5433/ezmsg` | Postgres connection |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection |
| `JWT_SECRET` | (auto-generated in dev) | Token signing key |
| `SIMULATION_MODE` | `true` | Skip real SMS/push delivery |

## License

MIT
