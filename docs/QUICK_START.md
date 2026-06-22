# Quick Start

Run the full local demo in one command after copying the environment file.

## Prerequisites

- Docker and Docker Compose
- Optional for local development: Node.js 20+, Python 3.12+

## Start the demo

```bash
git clone https://github.com/ardamoustafa1/SystemForge-AI.git
cd SystemForge-AI
cp .env.example .env
docker compose up --build
```

Open:

- Web app: http://localhost:3000
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

## Demo account

```text
Email: demo@systemforge.dev
Password: SystemForgeDemo123!
```

The demo seed job is idempotent and creates three showcase designs:

- Multi-tenant SaaS Control Plane
- Marketplace Order & Fulfillment Platform
- AI Workflow Automation Hub

## First product loop

1. Sign in with the demo account.
2. Open a seeded design from the dashboard.
3. Review the architecture sections, scorecard, checklist, and Mermaid diagram.
4. Export an artifact.
5. Create a new design brief and compare the output.

An OpenAI key is optional for local exploration. If no model key is configured, the deterministic fallback generator still creates schema-valid demo artifacts.

## Stop

```bash
docker compose down
```

Remove local volumes if you want a fresh seeded database:

```bash
docker compose down -v
```
