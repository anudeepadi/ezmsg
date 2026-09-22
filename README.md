# EzMsg — Messaging Protocols

A workspace for editing messaging protocols, enrolling participants and scheduling messages for research workflows. It combines a FastAPI API, Next.js administration interface and Python scheduler, originally built for the QuitTxt research study.

**Status:** application prototype with local simulation support. Deployment guides are included; this README does not claim a currently available hosted service or validated study deployment.

## Architecture

- [api/](api/) — authentication, projects, participants, protocol nodes and REST endpoints.
- [web/](web/) — protocol administration and scheduling interface.
- [worker/](worker/) — queued-message scheduler.
- [docker/docker-compose.yml](docker/docker-compose.yml) — PostgreSQL, Redis and application services.

## Local simulation

```bash
git clone https://github.com/anudeepadi/ezmsg.git
cd ezmsg
docker compose -f docker/docker-compose.yml up --build
```

The checked-in Compose file sets `SIMULATION_MODE=true` for API and worker. It exposes the frontend on `http://localhost:3000`, API on `http://localhost:8000`, API documentation on `/docs`, and PostgreSQL on local port 5433. The development seed identifies `admin@example.com` / `admin123`; these are local-demo credentials only.

Create a separate demo project with a synthetic participant such as `Demo Participant`, a welcome message, and one response branch. Open the protocol editor, step through the branch and inspect the scheduler/log output. Keep delivery in simulation mode and use synthetic records; this walkthrough does not require study participant data or real messages.

The [protocol test scripts](test_protocol_flow.py) and [multi-day scenarios](test_protocol_multiday.py) show the protocol-engine call shape, but depend on an initialized database and project records. They are integration scenarios, not a self-contained fixture.

## Developing components

For the API, create a Python 3.12 environment in `api/`, install with `pip install -e .`, configure database/Redis settings, then run `uvicorn app.main:app --reload --port 8000`. In `web/`, run `npm ci` followed by `npm run dev`. The worker uses its own `worker/pyproject.toml` and runs as `python -m app.main` from that directory.

Use the environment variable names in the [Compose file](docker/docker-compose.yml) and each service's settings as the source of truth. The Compose development defaults are not deployment credentials. For deployment context, see [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md); provider configuration and external delivery require their own validation.

## Protocol integration

The API includes `/v1/protocol/start` and `/v1/protocol/respond`. Use a configured API key and a project ID from your own database; prior example IDs and keys were tied to a local setup. The OpenAPI page provides request schemas when the API is running.

## Contribution and scope

This repository captures the API, protocol editor and scheduler implementation. QuitTxt is the motivating research context; no study outcomes, participant data or institution-wide deployment claims are published here. A separate authorship breakdown is not recorded, so no unverified individual/team responsibilities are assigned.

## License

MIT (as stated in the original project documentation).
