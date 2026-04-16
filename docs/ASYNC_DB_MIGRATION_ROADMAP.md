# Async DB Migration Roadmap

## Goal
Reduce sync DB pressure in async endpoints and worker hot paths.

## Phase 1 (Hot Paths)
1. `design create/regenerate` service paths to `AsyncSession`.
2. Export job enqueue/status/download paths to async repository layer.
3. Worker DB calls (`generation`, `delivery`) via async SQLAlchemy engine.

## Phase 2 (Auth + Workspace)
1. Auth session management (`refresh_token_sessions`) async repository.
2. Workspace member and role mutation paths async migration.

## Phase 3 (Full Cutover)
1. Replace `SessionLocal` usages in workers with async session factory.
2. Remove sync bridge shims for idempotency/rate-limit integrations.
3. Add regression perf tests for event-loop throughput and DB pool utilization.

## Success Metrics
- p95 API latency reduction on mutation routes.
- lower worker event processing jitter.
- reduced threadpool blocking under concurrent load.

