# 3-Minute Demo Script

This script is designed for maintainers, reviewers, and open-source visitors who want to see the product quickly.

## Start

```bash
cp .env.example .env
docker compose up --build
```

Open:

- Web app: http://localhost:3000
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

## Demo Credentials

The local Docker Compose stack runs an idempotent demo seed job.

```text
Email: demo@systemforge.dev
Password: SystemForgeDemo123!
```

You can override these with `DEMO_USER_EMAIL`, `DEMO_USER_PASSWORD`, `DEMO_USER_FULL_NAME`, and `DEMO_WORKSPACE_NAME` in `.env`.

## Tour

1. Sign in with the demo account.
2. Open the dashboard and review the seeded designs:
   - Multi-tenant SaaS Control Plane
   - Marketplace Order & Fulfillment Platform
   - AI Workflow Automation Hub
3. Open a design detail page.
4. Review the executive summary, runtime topology, security architecture, database plan, scorecard, and Mermaid diagram.
5. Try export actions for Markdown/PDF where enabled.
6. Create a new design brief. An OpenAI key is optional for local exploration; without one, the deterministic fallback generator still creates schema-valid demo output.

## What This Proves

- The repository can be explored without a paid model key.
- The architecture artifact is structured, not raw chat text.
- The UI demonstrates the main loop: brief → artifact → review → export.
- Seed data gives visitors something meaningful within minutes.
