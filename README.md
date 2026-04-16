# SystemForge AI

SystemForge AI is a full-stack AI engineering workspace that turns product requirements into structured, production-oriented system design artifacts.

It is deliberately built as an artifact-first platform rather than a generic chatbot. The core experience is centered on generating, reviewing, versioning, securing, and exporting architecture documents that engineering teams can actually use.

Repository: [github.com/ardamoustafa1/SystemForge-AI](https://github.com/ardamoustafa1/SystemForge-AI)

## Why This Project Exists

Teams often start architecture work in scattered docs, Slack threads, whiteboards, or AI chats that are hard to review and impossible to operationalize. SystemForge AI closes that gap by producing structured outputs with explicit trade-offs, diagrams, implementation checklists, and export flows.

The result is a workflow that is closer to an engineering design review system than a prompt playground.

## Core Value

- Transform raw product/backend requirements into consistent architecture artifacts
- Generate structured outputs instead of free-form chat responses
- Support review workflows with comments, review status, version history, and timelines
- Make architecture portable through Markdown, PDF, scaffold ZIP, Terraform ZIP, and task CSV exports
- Add workspace-aware ownership, role-based access, and operational/security visibility

## What You Get

### Product Capabilities

- AI-generated system design documents with strict schema validation
- Executive summary, requirements, architecture notes, trade-off decisions, and engineering checklist
- Mermaid diagram generation and in-app diagram editing/sync
- Cost estimation plus scenario-based cost analysis and calibration hooks
- Design review workflow with comments and approval states
- Shareable read-only public links for design artifacts
- Async export jobs and job-center style tracking
- Workspace management with budgets, roles, and member administration
- Security operations panels for abuse analytics, anomaly summaries, audit trail, and active sessions

### Engineering Capabilities

- Schema-first generation pipeline with safe fallback behavior
- FastAPI backend with modular services and strict Pydantic contracts
- Next.js App Router frontend with typed client-side API usage
- Realtime infrastructure over WebSocket + Redis Streams
- Background workers for generation, export, outbox relay, delivery, and notifications
- CI coverage for backend tests, frontend build/E2E, audits, and backend static checks

## Tech Stack

### Frontend

- Next.js 15
- React 19
- TypeScript
- Tailwind CSS
- SWR
- React Hook Form + Zod
- Mermaid
- Playwright + Vitest

### Backend

- FastAPI
- SQLAlchemy 2
- Pydantic 2
- PostgreSQL
- Redis
- Alembic
- Pytest
- Sentry SDK

### Infrastructure and Local Tooling

- Docker Compose
- Multi-service worker topology
- GitHub Actions CI

## System Overview

```text
User -> Next.js frontend -> FastAPI API -> PostgreSQL
                             |            -> Redis Streams / Redis cache
                             |
                             -> Generation worker
                             -> Export worker
                             -> Outbox relay worker
                             -> Delivery worker
                             -> Notification worker
```

### Main Application Areas

- `frontend/`: product UI, dashboard, auth flows, review UI, settings, workspace experience
- `backend/app/api/routes/`: REST API surface
- `backend/app/services/`: business logic for generation, export, authz, jobs, security, and workspaces
- `backend/app/workers/`: background workers and stream consumers
- `backend/alembic/`: database migrations
- `docs/`: ADRs, security docs, API governance, benchmark/load-test material

## Key Features

### 1. AI Design Generation

The user submits a structured design brief. The backend converts that brief into a strict prompt and expects a JSON response that must satisfy `DesignOutputPayload`. If the model fails or returns malformed output, the system can fall back to schema-valid safe output for local/test use.

Generated outputs include:

- executive summary
- functional and non-functional requirements
- high-level architecture
- architecture decisions
- trade-offs
- scorecard
- cost considerations
- recommended implementation phases
- engineering checklist
- Mermaid diagram

### 2. Architecture Review Workflow

Each design can move through review states and capture team feedback.

- review status: `draft`, `in_review`, `approved`, `changes_requested`
- comment threads on a design
- decision timeline
- version comparison and explain-diff flow
- notes editing and architecture diagram sync

### 3. Workspace-First Collaboration

Workspaces are first-class and shape authorization behavior across the product.

- list/create/update/delete workspaces
- set default workspace
- invite/remove members
- role management: `admin`, `editor`, `viewer`
- workspace token budget and alert threshold controls

### 4. Export and Delivery

Generated artifacts are not trapped in the UI.

- Markdown export
- PDF export
- scaffold ZIP export
- Terraform ZIP export
- engineering checklist CSV export for Jira/Linear-style workflows
- async export jobs with status and download endpoints

### 5. Security and Operational Visibility

The application includes security-aware product and platform behaviors.

- cookie-based auth with CSRF protection for mutating requests
- workspace-aware authorization checks
- abuse analytics summary
- anomaly summary
- audit trail endpoints
- refresh-token session visibility and revocation
- security response headers and API deprecation/version headers

## API Surface

### Auth

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `POST /api/auth/refresh`
- `GET /api/auth/me`
- `GET /api/auth/sessions`
- `DELETE /api/auth/sessions/{session_id}`

### Designs

- `POST /api/designs`
- `GET /api/designs`
- `GET /api/designs/{id}`
- `DELETE /api/designs/{id}`
- `POST /api/designs/{id}/regenerate`
- `PATCH /api/designs/{id}/notes`
- `PATCH /api/designs/{id}/architecture`
- `GET /api/designs/{id}/review`
- `PATCH /api/designs/{id}/review`
- `GET /api/designs/{id}/comments`
- `POST /api/designs/{id}/comments`
- `GET /api/designs/{id}/timeline`
- `GET /api/designs/{id}/cost-calibration`
- `POST /api/designs/{id}/cost-analysis`

### Design Versions and Sharing

- `GET /api/designs/{id}/versions`
- `GET /api/designs/{id}/versions/{version_id}`
- `GET /api/designs/{id}/versions/compare`
- `GET /api/designs/{id}/versions/explain`
- `GET /api/designs/{id}/share`
- `POST /api/designs/{id}/share`
- `DELETE /api/designs/{id}/share`
- `GET /api/public/share/{token}`
- `GET /api/public/share/{token}/export`

### Exports

- `GET /api/designs/{id}/export?format=markdown|pdf`
- `POST /api/designs/{id}/export-jobs?format=pdf|markdown`
- `GET /api/designs/export-jobs/{job_id}`
- `GET /api/designs/export-jobs/{job_id}/download`
- `GET /api/designs/{id}/export/scaffold`
- `GET /api/designs/{id}/export/terraform`
- `GET /api/designs/{id}/export/tasks-csv?provider=jira|linear`

### Workspaces

- `GET /api/workspaces`
- `POST /api/workspaces`
- `GET /api/workspaces/{workspace_id}`
- `PATCH /api/workspaces/{workspace_id}`
- `DELETE /api/workspaces/{workspace_id}`
- `POST /api/workspaces/{workspace_id}/default`
- `GET /api/workspaces/{workspace_id}/budget`
- `PATCH /api/workspaces/{workspace_id}/budget`
- `POST /api/workspaces/{workspace_id}/members`
- `PATCH /api/workspaces/{workspace_id}/members/{member_id}`
- `DELETE /api/workspaces/{workspace_id}/members/{member_id}`

### Dashboard, Security, Health, Advanced

- `GET /api/dashboard/ops-summary`
- `GET /api/security/abuse-summary`
- `GET /api/security/anomaly-summary`
- `GET /api/security/audit-trail`
- `GET /api/health`
- `GET /api/health/ready`
- `GET /api/health/api-versions`
- `GET /api/ws`

## Realtime Architecture

SystemForge AI includes a Redis Streams-based realtime layer for messaging and fanout.

### Important Streams

- `sf:rt:v1:stream:delivery`
- `sf:rt:v1:stream:realtime:{user_id}`
- `sf:rt:v1:stream:notify`
- `sf:rt:v1:stream:notify:delayed`

### Worker Responsibilities

- `backend-outbox-worker`: publishes DB outbox events into Redis Streams
- `backend-delivery-worker`: routes realtime events to active users or notification queues
- `backend-notification-worker`: handles push notification delivery/retries
- `backend-generation-worker`: processes async design generation jobs
- `backend-export-worker`: processes async export jobs

### Realtime Flow

1. Client opens WebSocket connection at `GET /api/ws`.
2. Client sends `session.hello`.
3. Gateway validates/authenticates and returns `session.welcome`.
4. Client sends messages/events.
5. Backend persists durable state and writes outbox records.
6. Relay and delivery workers fan out events through Redis Streams.
7. Notification worker handles offline delivery scenarios.

## Repository Structure

```text
systemforge-ai/
├─ .github/workflows/         # CI pipelines
├─ backend/
│  ├─ alembic/                # DB migrations
│  ├─ app/
│  │  ├─ api/routes/          # REST endpoints
│  │  ├─ auth/                # auth dependencies and services
│  │  ├─ core/                # config, security, metrics, infra glue
│  │  ├─ db/                  # DB session/base setup
│  │  ├─ llm/                 # prompts, fallback, output processing
│  │  ├─ models/              # SQLAlchemy models
│  │  ├─ notifications/       # provider integration
│  │  ├─ realtime/            # websocket gateway
│  │  ├─ schemas/             # Pydantic contracts
│  │  ├─ services/            # business logic
│  │  └─ workers/             # background workers
│  ├─ requirements.txt
│  └─ Dockerfile
├─ docs/                      # ADRs, security, governance, reports
├─ frontend/
│  ├─ app/                    # Next.js app router pages
│  ├─ components/             # reusable UI components
│  ├─ features/               # feature-level client logic
│  ├─ lib/                    # API client, context, helpers
│  ├─ types/                  # frontend types
│  ├─ package.json
│  └─ Dockerfile
├─ SECURITY.md
├─ Makefile
├─ docker-compose.yml
└─ README.md
```

## Quick Start

### Option A: Docker Compose

1. Copy the root environment file:

```bash
cp .env.example .env
```

2. Start the full stack:

```bash
docker compose up --build
```

3. Open the app:

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health endpoint: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### Useful Make Targets

```bash
make up
make down
make rebuild
make logs
```

## Local Development Without Docker

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

### Required Local Services

- PostgreSQL
- Redis

## Environment Variables

### Root `.env.example`

These values are used by `docker-compose.yml`.

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `BACKEND_DATABASE_URL`
- `BACKEND_REDIS_URL`
- `BACKEND_JWT_SECRET`
- `BACKEND_OPENAI_API_KEY`
- `BACKEND_OPENAI_BASE_URL`
- `BACKEND_OPENAI_MODEL`
- `BACKEND_AUTO_CREATE_TABLES`
- `FRONTEND_NEXT_PUBLIC_API_URL`
- `FRONTEND_NEXT_PUBLIC_APP_NAME`

### Important Runtime Notes

- `OPENAI_BASE_URL` / `BACKEND_OPENAI_BASE_URL` can be used with OpenAI-compatible providers
- production should use a strong `JWT_SECRET`
- `AUTO_CREATE_TABLES` should remain `false` outside local dev/test
- `PUBLIC_APP_URL` should point to the frontend origin for public share links

## Database and Migrations

Use Alembic for schema changes.

```bash
cd backend
alembic upgrade head
```

Docker-safe helper:

```bash
docker compose run --rm backend sh -lc "/app/scripts/migrate.sh"
```

Important behavior:

- the backend hard-fails in non-dev environments if insecure security settings are detected
- Compose includes a `backend-migrate` one-shot service
- backend and workers depend on migration completion before starting

## Testing and Quality Gates

### Backend

```bash
docker compose run --rm backend-test
```

Or locally:

```bash
cd backend
pytest tests -q
```

### Frontend

```bash
cd frontend
npm run build
npm run test
npm run test:e2e
```

### CI

GitHub Actions currently runs:

- backend static checks (`ruff`, `pyre`)
- backend tests in Docker
- frontend type/build/E2E flow
- dependency audits

## Security Model

SystemForge AI includes several baseline security measures:

- HTTP-only cookie auth for browser sessions
- CSRF protection on mutating endpoints
- security response headers
- request-size enforcement for generation payloads
- workspace-aware authorization checks
- ownership checks on export jobs and design access
- session revocation APIs
- public share links with read-only token-based access

See also: [SECURITY.md](SECURITY.md)

## Documentation

Architecture, governance, and security docs live under `docs/`.

- [Case Study](docs/CASE_STUDY.md)
- [ADR-001 Workspace-First Authz](docs/ADR-001-workspace-first-authz.md)
- [Threat Model](docs/THREAT_MODEL.md)
- [Security Posture](docs/SECURITY_POSTURE.md)
- [Benchmark Plan](docs/BENCHMARK_PLAN.md)
- [API Versioning Policy](docs/API_VERSIONING.md)
- [API Governance Playbook](docs/API_CONTRACT_GOVERNANCE_PLAYBOOK.md)
- [Load Test Report](docs/LOAD_TEST_REPORT.md)
- [Authz Contract Matrix](docs/AUTHZ_CONTRACT_MATRIX.md)
- [Async DB Migration Roadmap](docs/ASYNC_DB_MIGRATION_ROADMAP.md)
- [Secrets Rotation & Break-Glass](docs/SECRETS_ROTATION_BREAK_GLASS.md)
- [WebSocket Fanout Simplification](docs/WEBSOCKET_FANOUT_SIMPLIFICATION.md)

## Current Scope and Limitations

- Playwright coverage is intentionally a smoke suite, not a full regression matrix
- some advanced operational wiring is environment-dependent
- WebSocket fanout can still be simplified for very high-concurrency deployments
- this repository is optimized for local/full-stack engineering showcase and product iteration

## Portfolio Positioning

This project supports a statement like:

> Built an AI-powered engineering workspace that transforms product requirements into production-grade architecture artifacts with review workflows, exports, workspace-based authorization, realtime infrastructure, and full-stack operational tooling using FastAPI, Next.js, PostgreSQL, Redis, and LLM pipelines.

## License

No license file is currently included in the repository. Add one if you want to make usage terms explicit.
