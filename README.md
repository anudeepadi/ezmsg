# EzMsg — Messaging Protocol Management System

A full-stack platform for managing multi-day, personalized messaging protocols in health interventions. Built for the **QuitTxt Research Study** (UTSA smoking cessation) with bilingual support (EN/ES).

```
Frontend (Next.js 14)          Mobile Apps (RN / Flutter / Swift)
        |                                |
        +----------------+---------------+
                         v
              FastAPI Backend (Python 3.12)
              ~70 routes, JWT auth, Protocol engine
                         |
          +--------------+------------------+
          v              v                  v
     PostgreSQL      Redis Cache      Worker (Scheduler)
     (Supabase)      (Upstash)        Background delivery
                                           |
                                     +-----+-----+
                                     v           v
                                  Twilio       FCM
                                  (SMS)     (Push Notif)
```

## Project Structure

```
ezmsg-new/
  api/            FastAPI backend, 19 SQLAlchemy models, JWT auth
  web/            Next.js 14 admin dashboard
  worker/         Background scheduler for message delivery
  docker/         Docker Compose for local development
```

## Quick Start (Local Development)

See **[DEVELOPMENT.md](./DEVELOPMENT.md)** for full setup instructions.

```bash
# Option 1: Docker (easiest)
cd docker && docker-compose up -d

# Option 2: Manual
cp .env.local.example .env.local   # Fill in DB credentials
cd api && pip install -e . && uvicorn app.main:app --reload
```

## Deployment

See **[DEPLOYMENT.md](./DEPLOYMENT.md)** for Railway deployment guide.

**Services to deploy:**
| Service | Dockerfile | Port | Purpose |
|---------|-----------|------|---------|
| API | `api/Dockerfile` | 8000 | REST API + Protocol engine |
| Worker | `worker/Dockerfile` | none | Background message delivery |
| Web | `web/Dockerfile` | 3000 | Admin dashboard |

**External services:** PostgreSQL (Supabase), Redis (Upstash)

## Protocol API (Mobile Integration)

See **[MOBILE_APP_INTEGRATION.md](./MOBILE_APP_INTEGRATION.md)** for mobile developer guide.

```bash
# Start a protocol session
curl -X POST https://your-api.railway.app/v1/protocol/start \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $PROTOCOL_API_KEY" \
  -d '{"project_id": 7, "language": "en"}'

# Send a response
curl -X POST https://your-api.railway.app/v1/protocol/respond \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $PROTOCOL_API_KEY" \
  -d '{"session_id": "uuid-here", "response": "1"}'
```

## Features

**Admin Dashboard** — Project/participant management, visual node graph editor, bilingual template editor, analytics, scheduler monitoring

**Protocol Engine** — Stateful session management (Redis-backed), conditional branching, timing/scheduling, variable substitution, keyword handling (STOP, HELP, etc.)

**Message Delivery** — FCM push notifications, Twilio SMS, exponential backoff retries (8 max), idempotency keys, simulation mode for testing

**Security** — JWT (HS256) via HttpOnly cookies, RBAC (Admin/Researcher/Operator), rate limiting, bcrypt password hashing

## API Endpoints

| Group | Prefix | Key Routes |
|-------|--------|------------|
| Auth | `/v1/auth` | login, register, refresh, logout, me |
| Admin | `/v1/admin` | Projects, Participants, Templates, Nodes, Variables, Analytics |
| Protocol | `/v1/protocol` | start, respond, session status (API key auth) |
| Public | `/v1/public` | Enrollment, participant status, FCM token, language switch |
| Scheduler | `/v1/scheduler` | Queue health, requeue, abort |
| Webhooks | `/v1/webhooks` | Twilio inbound/status, FCM token refresh, quick replies |

## Database (19 tables)

Core tables: `users`, `projects`, `participants`, `message_templates`, `message_template_texts`, `messaging_nodes`, `messaging_node_edges`, `scheduled_messages`, `variables`, `participant_variable_values`, `timing_elements`, `conditional_expressions`, `incoming_messages`, `sms_keywords`, `available_languages`

## Environment Variables

See `.env.local.example` (development) and `.env.railway.example` (production).

**Required in production:** `JWT_SECRET`, `PROTOCOL_API_KEY`, `DATABASE_URL`, `REDIS_URL`

## QuitTxt V9 Protocol Data

| Item | Count |
|------|-------|
| Messaging nodes | 63 |
| Message templates | 61 (bilingual EN/ES) |
| Variables | 12 |
| Timing elements | 14 |
| Keywords | 20+ (EN + ES) |

Import script: `api/scripts/import_quittxt_v9_protocol.py`

## License

MIT
