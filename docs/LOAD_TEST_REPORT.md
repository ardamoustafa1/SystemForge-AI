# Load Test Report

This file records reproducible benchmark evidence. Results must be read together with the tested endpoint and environment; a health-check benchmark is not a generation/export capacity claim.

## 2026-06-22 — Local Health Endpoint Smoke Benchmark

Status: **passed**, suitable as local HTTP-stack smoke evidence. Not yet sufficient for a public production performance claim.

### Environment

| Field | Value |
|---|---|
| Base commit | `d552d33` plus the current uncommitted P2 hardening changes |
| Date | 2026-06-22 |
| Host | macOS Darwin ARM64 |
| Host CPU / memory | Apple M4 / 16 GiB |
| Docker allocation | Docker Desktop allocation not recorded; do not equate host memory with container limits |
| Docker | Client 29.2.0 / Server 29.2.0 |
| Backend topology | One FastAPI/Uvicorn API container |
| Database / Redis | PostgreSQL 16 / Redis 7 |
| Dataset | Seeded demo user, one workspace, three architecture designs |
| k6 image | `grafana/k6@sha256:632ddbc81a4a9fdc9e597da91ab1d8fcf1916dd988b43b4a4559d2f8d8e73d47` |
| Scenario | `load-test/k6-script.js` against `GET /api/health` |
| Stages | 30s ramp to 50 VUs, 60s ramp to 100 VUs, 30s ramp down |

### Results

| Metric | Result |
|---|---:|
| Completed requests | 6,730 |
| Average throughput | 56.01 requests/second |
| Peak active VUs observed | 99 |
| Median latency | 4.88 ms |
| p90 latency | 11.81 ms |
| p95 latency | 14.68 ms |
| Maximum latency | 138.05 ms |
| Request error rate | 0.00% |
| Failed checks | 0 / 6,730 |
| Observed 5xx responses | 0 |

Thresholds passed:

- `http_req_duration: p(95) < 200 ms`
- `http_req_failed: rate < 1%`

Reproduce:

```bash
docker compose up --build
docker run --rm -i \
  -e BASE_URL=http://host.docker.internal:8000/api \
  grafana/k6 run - < load-test/k6-script.js
```

## Required Release Benchmarks

The authenticated mixed-workload scenario remains the release-quality gate:

```bash
BASE_URL=http://localhost:8000/api \
AUTH_COOKIE='sf_access_token=...; sf_csrf_token=...' \
CSRF='...' \
WORKSPACE_ID='1' \
k6 run ops/loadtest/k6-systemforge.js
```

Before making a production performance claim, record these separately:

| Workload | Required evidence |
|---|---|
| Design create/regenerate | RPS, p50/p95/p99 completion latency, provider mode, fallback rate |
| Markdown/PDF/scaffold exports | Throughput, p95/p99 latency, artifact size, failures |
| Worker queues | Queue depth, lag, retries, dead-letter count |
| WebSocket | Concurrent connections, fanout p95, reconnect storm behavior |
| Database | CPU, connections, slow queries, lock waits |

## Release Targets

| Metric | Target |
|---|---:|
| API 5xx rate | < 0.5% |
| Design create p95 | < 30s |
| Markdown export p95 | < 10s |
| PDF export p95 | < 25s |
| Worker queue lag | < 5s |

Do not generalize the health endpoint result into a generation, export, database, or WebSocket capacity claim.
