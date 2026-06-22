# Showcase Examples

These examples are the “why should I star this?” layer of the project. Each one maps a realistic product brief to the kind of architecture artifact SystemForge AI is built to produce.

Browse the concrete export files in [`examples/`](../examples/README.md).

## 1. Multi-tenant SaaS Control Plane

**Brief:** A B2B SaaS product needs workspace isolation, RBAC, audit trails, token budgets, and background job visibility.

**Generated architecture emphasis:**

- Tenant-safe data boundaries through workspace membership.
- API layer with CSRF, rate limits, quotas, and idempotency.
- PostgreSQL for durable state; Redis Streams for job fanout.
- Worker topology for generation/export/notification.
- Review states and comments for architecture approval.

**Useful outputs:**

- Architecture summary for engineering review.
- Mermaid runtime topology.
- Implementation checklist.
- Markdown/PDF artifact for PRD handoff.

## 2. Marketplace Order & Fulfillment Platform

**Brief:** Buyers place orders, sellers manage inventory, payment providers send webhooks, and fulfillment status updates need realtime visibility.

**Generated architecture emphasis:**

- Idempotent payment webhook ingestion.
- Race-safe inventory reservations.
- Async fulfillment events.
- Seller dashboard and buyer status fanout.
- Critical-data security posture.

**Useful outputs:**

- Checkout and webhook flow.
- Database entity plan.
- Failure recovery checklist.
- Terraform/Docker/Kubernetes export direction.

## 3. AI Workflow Automation Hub

**Brief:** Teams compose AI workflows, queue model calls, enforce token budgets, retry failed jobs, and export architecture artifacts.

**Generated architecture emphasis:**

- Provider abstraction and fallback strategy.
- Queue backpressure and usage limits.
- Observability around latency, queue depth, provider errors, and fallback rate.
- Artifact versioning and review workflow.

**Useful outputs:**

- AI inference orchestration plan.
- Cost and quota strategy.
- Observability/SLO recommendations.
- Exportable implementation roadmap.

## Example Export Snippets

### Docker Compose Direction

```yaml
services:
  api:
    image: ghcr.io/your-org/systemforge-api:0.1.0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
  worker:
    image: ghcr.io/your-org/systemforge-api:0.1.0
    command: ["python", "-m", "app.workers.run_generation_worker"]
```

### Terraform Direction

```hcl
module "postgres" {
  source = "./modules/postgres"
  name   = "systemforge"
}

module "redis" {
  source = "./modules/redis"
  name   = "systemforge-events"
}
```

### Kubernetes Direction

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: systemforge-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: systemforge-backend
```

The repository also contains implementation-oriented export services under `backend/app/services`, deployable project assets under `ops`, and concrete showcase exports under `examples`. Treat them as reviewable starting points, not a substitute for your production review.
