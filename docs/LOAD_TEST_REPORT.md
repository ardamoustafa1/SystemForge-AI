# Load Test Report

## Objective
Validate throughput and latency for design generation, export jobs, and websocket session handling under controlled load.

## Method
- Tooling: `k6` and backend worker telemetry.
- Scenarios:
  - Authenticated design create/regenerate burst
  - Export job queue burst (PDF + Markdown)
  - Concurrent websocket heartbeats and typing events

## Result Template (fill per run)
- Test date:
- Commit SHA:
- Environment:
- Virtual users:
- Duration:

### Key Metrics
- Generation p95 latency:
- Generation error rate:
- Export queue lag max:
- Websocket disconnect rate:
- High severity abuse events:

## Pass/Fail Criteria
- Generation p95 <= 15s
- Generation error rate < 2%
- Export queue lag returns to baseline within 10m
- Websocket disconnect rate < 1%

## Observations
- 

## Action Items
- 

