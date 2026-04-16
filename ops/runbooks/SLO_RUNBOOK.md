# SystemForge SLO Runbook

## Scope
- Generation latency SLO
- Export queue lag SLO
- Abuse event spike response

## SLO Targets
- Generation p95 latency: <= 15s
- Generation failure rate: < 2%
- Export queue lag: <= 5 pending/min sustained

## Incident Workflow
1. Confirm active alerts in Grafana/Alertmanager.
2. Check `/api/health/metrics` and `/api/security/abuse-summary`.
3. Identify whether bottleneck is API, worker, Redis, or DB.
4. Apply mitigation:
   - Increase worker replicas for generation/export.
   - Temporarily reduce per-user generation rate limit.
   - Enable stricter abuse policy (`prompt_abuse_policy_mode=challenge|block`).
5. Validate SLO recovery for 15 minutes before closing.

## Common Mitigations
- **High generation latency**
  - Scale generation worker replicas.
  - Verify LLM provider latency.
  - Enforce tighter prompt payload limits.
- **Export queue lag**
  - Scale export worker.
  - Pause non-critical bulk exports.
  - Inspect failed export jobs for retry storms.
- **Abuse spikes**
  - Rotate to block mode for prompt abuse policy.
  - Tighten websocket and API rate limits.
  - Revoke compromised sessions (`token_version` bump for affected users).

## Postmortem Requirements
- Detection time and alert signal
- User impact window
- Root cause and contributing factors
- Permanent fixes and owner

