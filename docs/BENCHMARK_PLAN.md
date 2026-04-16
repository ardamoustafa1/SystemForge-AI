# Benchmark and Load-Test Plan

## Goals
- Validate generation latency under concurrent load
- Measure export job throughput and tail latency
- Observe websocket saturation thresholds

## Core SLO Targets
- P95 generation completion latency < 30s
- Export job completion P95 < 10s for markdown, < 25s for PDF
- API 5xx error rate < 0.5%
- Queue lag < 5s for generation/export streams

## Scenarios
1. Burst create/regenerate requests (10, 25, 50 concurrent users)
2. Export workload spike (PDF-heavy)
3. Mixed traffic (generate + exports + websocket sessions)

## Metrics Required
- `sf_http_requests_total`
- `sf_http_request_errors_total`
- `sf_http_request_latency_ms_sum`
- `sf_worker_events_total` by worker/event

## Reporting
- Include p50/p95/p99 latency
- Include queue lag snapshots
- Record failure signatures and mitigation actions
