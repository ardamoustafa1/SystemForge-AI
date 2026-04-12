# SystemForge AI

SystemForge AI is an AI-powered engineering platform that transforms product ideas and backend requirements into structured, production-oriented system design documents.

This project is intentionally **not** a chatbot wrapper. It is an artifact-first architecture workspace with scoring, trade-off analysis, diagram support, and exportable design outputs.

## Product Overview

- Converts requirements into consistent engineering design artifacts
- Produces structured sections (requirements, architecture, trade-offs, scorecards, implementation checklist)
- Renders Mermaid architecture diagrams in the review document
- Maintains design history for reuse and iteration
- Supports markdown export and downloadable PDF (Unicode text via DejaVu; optional rendered Mermaid PNG page via [Kroki](https://kroki.io), disable with `MERMAID_PDF_RENDER_ENABLED=false` for air-gapped environments)

## Architecture Summary

### Frontend
- Next.js App Router
- TypeScript
- Tailwind CSS + shadcn-style component structure
- React Hook Form + Zod validation
- Mermaid rendering for architecture diagrams

### Backend
- FastAPI
- Pydantic schemas for strict input/output contracts
- SQLAlchemy ORM
- JWT auth + password hashing
- Modular services for generation, designs, and exports

### Data and Infra
- PostgreSQL for core persistence
- Redis for realtime streams, presence/session routing, and background workflows
- Docker + docker-compose for local environment parity

## Realtime Messaging Architecture

### Components
- `backend` exposes WebSocket gateway at `GET /api/ws` and REST APIs.
- PostgreSQL stores durable message state (`conversations`, `messages`, `message_recipients`) and `outbox_events`.
- Redis Streams are used as the realtime/event pipeline:
  - `sf:rt:v1:stream:delivery`
  - `sf:rt:v1:stream:realtime:{user_id}`
  - `sf:rt:v1:stream:notify`
  - `sf:rt:v1:stream:notify:delayed` (zset-backed delayed queue)
- Workers:
  - `backend-outbox-worker` (DB outbox -> Redis Streams)
  - `backend-delivery-worker` (delivery fanout / offline routing)
  - `backend-notification-worker` (mock push provider + retry handling)

### Short Flow
1. Client connects WebSocket and sends `session.hello`.
2. Gateway validates/authenticates and returns `session.welcome`.
3. Client sends `message.send`.
4. Backend persists message + recipients + outbox event in one DB transaction.
5. Outbox relay publishes `message.created` into delivery stream.
6. Delivery worker routes:
   - online recipient -> `message.new` to `realtime:{user_id}` stream
   - offline recipient -> enqueue into notify stream
7. Recipient acks `message.delivered` / `message.read`; backend persists and emits outbox events for downstream fanout.

## Repository Structure

```text
systemforge-ai/
├─ backend/
│  ├─ app/
│  │  ├─ api/routes/
│  │  ├─ auth/
│  │  ├─ core/
│  │  ├─ db/
│  │  ├─ llm/
│  │  ├─ models/
│  │  ├─ schemas/
│  │  ├─ services/
│  │  └─ main.py
│  ├─ .env.example
│  ├─ requirements.txt
│  └─ Dockerfile
├─ frontend/
│  ├─ app/
│  ├─ components/
│  ├─ features/
│  ├─ lib/
│  ├─ types/
│  ├─ .env.example
│  ├─ package.json
│  └─ Dockerfile
├─ docs/
├─ docker-compose.yml
├─ .env.example
└─ README.md
```

## Core Backend APIs

### Auth
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

### Designs
- `POST /api/designs`
- `GET /api/designs`
- `GET /api/designs/{id}`
- `DELETE /api/designs/{id}`
- `POST /api/designs/{id}/regenerate` (placeholder contract)
- `GET /api/designs/{id}/export?format=markdown|pdf`

### Health
- `GET /api/health`
- `GET /api/health/ready`

## Environment Variables

### Root `.env.example` (for docker-compose)
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `BACKEND_DATABASE_URL`
- `BACKEND_REDIS_URL`
- `BACKEND_JWT_SECRET`
- `BACKEND_OPENAI_API_KEY`
- `BACKEND_OPENAI_MODEL`
- `BACKEND_AUTO_CREATE_TABLES`
- `FRONTEND_NEXT_PUBLIC_API_URL`
- `FRONTEND_NEXT_PUBLIC_APP_NAME`

### Backend `.env.example`
- `APP_NAME`
- `APP_ENV`
- `API_PREFIX`
- `CORS_ORIGINS`
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `JWT_EXP_MINUTES`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `RATE_LIMIT_PER_MINUTE`
- `AUTO_CREATE_TABLES`
- `NOTIFICATION_PROVIDER_MODE` (`mock` or `webhook`)
- `NOTIFICATION_PROVIDER_TIMEOUT_SECONDS`
- `NOTIFICATION_FCM_WEBHOOK_URL`
- `NOTIFICATION_APNS_WEBHOOK_URL`

### Frontend `.env.example`
- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_APP_NAME`

## Local Development

### Option A: Docker (recommended)
1. Copy root env:
   - `cp .env.example .env`
2. Run database migrations:
   - `docker compose run --rm backend sh -lc "/app/scripts/migrate.sh"`
3. Start services:
   - `docker compose up --build`
4. Open:
   - Frontend: `http://localhost:3000`
   - Backend docs: `http://localhost:8000/docs`

### Run database migrations
From `backend/`:
- `alembic upgrade head`
- Docker-safe helper (handles baseline stamp when needed):
  - `docker compose run --rm backend sh -lc "/app/scripts/migrate.sh"`

For local-only quick bootstrapping, `AUTO_CREATE_TABLES=true` can be used **only** in `development`/`test`.
The backend now hard-fails startup if `AUTO_CREATE_TABLES=true` is set in non-dev environments.
For docker-compose in this repository, `AUTO_CREATE_TABLES` is disabled and migrations are required.
Compose also includes a one-shot `backend-migrate` service; backend/workers wait for it with `service_completed_successfully`.

### Migration revisions relevant to realtime
- `0002_realtime_messaging_phase1`: realtime messaging tables + outbox table.
- `0003_outbox_relay_hardening`: outbox processing fields/indexes.
- `0004_realtime_messaging_indexes`: sequence/index hardening.
- `0005_notification_delivery_tbls`: notification devices + notification attempt logs.

## Realtime/Worker Topology

- `backend` serves HTTP + WebSocket gateway (`/api/ws`)
- `backend-outbox-worker` publishes `outbox_events` into Redis Streams
- `backend-delivery-worker` consumes `sf:rt:v1:stream:delivery`
  - active users -> writes to `sf:rt:v1:stream:realtime:{user_id}`
  - offline users -> enqueues to `sf:rt:v1:stream:notify`
- `backend-notification-worker` consumes `sf:rt:v1:stream:notify` and sends mock FCM/APNs
- delayed notification retries are stored in `sf:rt:v1:stream:notify:delayed` and promoted when due

### Run workers manually (non-Docker)
From `backend/` (after DB + Redis are running and migrations applied):
- Outbox relay: `python -m app.workers.run_outbox_relay`
- Delivery worker: `python -m app.workers.run_delivery_worker`
- Notification worker: `python -m app.workers.run_notification_worker`

### Option B: Run services individually
1. Start Postgres + Redis locally.
2. Backend:
   - `cd backend`
   - `cp .env.example .env`
   - `pip install -r requirements.txt`
   - `uvicorn app.main:app --reload`
3. Frontend:
   - `cd frontend`
   - `cp .env.example .env.local`
   - `npm install`
   - `npm run dev`

## Testing

### Backend tests
- `cd backend`
- `pip install -r requirements.txt`
- `python -m pytest tests -q`

### Backend tests with Docker
- `docker compose run --rm backend-test`

### Frontend tests
- `cd frontend`
- `npm install`
- `npm run test`

## Setup Notes

- Production path should use Alembic migrations and keep `AUTO_CREATE_TABLES=false`.
- Cookie auth is used with:
  - `httpOnly` access token cookie
  - SameSite policy via config
  - CSRF double-submit token for mutating requests
- If no OpenAI key is provided, generation falls back to a schema-valid demo output for local testing.

## Realtime Implementation Status (Truthful)

### Implemented
- WebSocket protocol envelope + runtime validation on backend/frontend.
- Session lifecycle basics: `session.hello`, `session.welcome`, heartbeat (`presence.heartbeat`/`pong`).
- Durable message write path with idempotency (`sender_user_id`, `client_msg_id`).
- Recipient row creation and authorization checks for delivered/read acknowledgements.
- Transactional outbox pattern and outbox relay worker with retry-safe status transitions.
- Delivery worker fanout to online users and offline notification enqueue.
- Notification worker with delayed retry scheduling and mock provider boundary.
- Sync replay endpoint behavior via `sync.request` backed by durable DB history.
- Backend tests for protocol/service flow and integration-style happy-path coverage.

### Partial / intentionally bounded
- `session.resume` is now server-side replay capable for bounded per-conversation windows; clients may still call `sync.request` when replay windows are truncated (`requires_sync=true`).
- `delivery.updated` and `read.updated` are fanned out through the delivery stream worker path to active conversation members.
- Push integration supports `mock` and `webhook` provider modes; first-party FCM/APNs SDK adapters and full token-management product flows remain future work.
- Frontend realtime UI is functional for protocol flow validation, but still marked experimental for full chat-product UX.

## How Generation Works

1. Frontend submits structured design input.
2. Backend builds a strict engineering prompt.
3. OpenAI returns JSON; parser validates against `DesignOutputPayload`.
4. On malformed output/provider failure, safe fallback output is used.
5. Design input/output is persisted and rendered in a review-document UI.
6. Export service builds markdown and can render a PDF for download (text plus optional diagram image).

## CI and testing

- **Backend:** `docker compose run --rm backend-test` (pytest, integration + unit).
- **Frontend:** `cd frontend && npm run build && npm run test:e2e` (Playwright smoke against `next start`).
- GitHub Actions (`.github/workflows/ci.yml`) runs both on push/PR to `main`/`master`.

Security practices for keys, share links, and reporting: see [SECURITY.md](SECURITY.md).

## Showcase Features

- Premium landing page with clear product differentiation
- Auth-protected engineering workspace
- Structured new-design flow with strong validation
- Design review page with scorecard + Mermaid toggle (rendered/raw)
- Project history with search and metadata
- Export-ready architecture document output

## Future Improvements

- Async regeneration/export jobs with Celery + Redis
- Richer PDF output (typography, branded templates; diagrams are already optional via Kroki)
- Team/workspace support with role-based permissions
- Usage analytics and audit trails
- Advanced filter facets and saved views in project history

## Current Limitations

- Regeneration currently executes synchronously and should be moved to a queued async job model for high-load environments.
- Playwright E2E is intentionally a small smoke suite; deep product flows are not fully covered.
- `AUTO_CREATE_TABLES` exists only for local convenience and should remain disabled in production.
- Full resume replay and delivery/read update fanout remain in-progress realtime milestones.

## Portfolio / CV Positioning

This project supports a credible statement like:

> Built an AI-powered system design platform that transforms startup ideas and backend requirements into structured production-grade architecture documents with trade-off analysis, scorecards, and visual diagrams using FastAPI, Next.js, PostgreSQL, Redis, and LLM workflows.

Recommended emphasis in interviews:
- schema-first AI generation (not generic chat)
- clean full-stack modular architecture
- production-style auth, ownership checks, and export pipeline design
- polished UX with strong error/empty/loading states and document-review experience
