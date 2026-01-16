# EzMsg - Messaging Protocol Management System

A full-stack application for managing messaging protocols in health interventions, built for the QuitTxt Research Study.

## Architecture

```
ezmsg-new/
├── api/          # FastAPI backend (Python 3.12)
├── web/          # Next.js 14 frontend (React 18)
├── worker/       # Background scheduler (Python 3.12)
└── docker/       # Docker configuration
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.12+ (for local backend development)

### Running with Docker

1. Start all services:

```bash
cd docker
docker-compose up -d
```

2. Access the applications:
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

3. Default credentials:
   - Email: `admin@example.com`
   - Password: `admin123`

### Local Development

#### Backend (API)

```bash
cd api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Start the server
uvicorn app.main:app --reload --port 8000
```

#### Frontend (Web)

```bash
cd web

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend proxies API requests to `http://localhost:8000`.

#### Worker

```bash
cd worker

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .

# Run in simulation mode
EZMSG_SIMULATION_MODE=true python -m app.main
```

## Features

### Admin Dashboard
- Project management (CRUD)
- Participant enrollment and tracking
- Message template creation with i18n (EN/ES)
- Node graph editor for messaging workflows
- Variable management for personalization
- Analytics and delivery statistics
- Scheduler monitoring

### Messaging Engine
- Scheduled message processing
- FCM push notifications (for Flutter app)
- Variable substitution in templates
- Quick reply handling
- Keyword processing (STOP, HELP, etc.)
- Exponential backoff retry logic

### API Endpoints

#### Authentication (`/v1/auth/*`)
- `POST /login` - Login with email/password
- `POST /logout` - Logout
- `POST /refresh` - Refresh access token
- `GET /me` - Get current user

#### Admin (`/v1/admin/*`)
- Projects, Participants, Templates, Nodes, Variables
- Analytics (overview, delivery stats)

#### Scheduler (`/v1/scheduler/*`)
- Queue health monitoring
- Message requeue/abort operations

#### Webhooks (`/v1/webhooks/*`)
- Twilio SMS inbound/status
- FCM token refresh
- App quick replies

## Database Schema

The system uses PostgreSQL with the following core tables:

- `users` - System users (admin, researcher, operator)
- `projects` - Study containers
- `participants` - Enrolled recipients
- `variables` / `participant_variable_values` - Personalization
- `message_templates` / `message_template_texts` - i18n content
- `messaging_nodes` / `messaging_node_edges` - Workflow graph
- `scheduled_messages` - Worker queue
- `incoming_messages` - Inbound message log
- `keywords` - Keyword triggers

## Environment Variables

### API
```env
EZMSG_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ezmsg
EZMSG_SECRET_KEY=your-secret-key-here
EZMSG_DEBUG=false
```

### Worker
```env
EZMSG_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ezmsg
EZMSG_SIMULATION_MODE=true
EZMSG_POLL_INTERVAL_SECONDS=5
EZMSG_BATCH_SIZE=50
```

## Design System

The frontend uses a light theme inspired by arnaud.ai:

- **Typography**: Source Serif 4 (headings), Inter (body), JetBrains Mono (code)
- **Colors**: Light background (#fafafa), subtle borders, sophisticated contrast
- **Components**: Minimal, clean interfaces with generous whitespace

## License

MIT
