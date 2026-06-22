# Worker Queue Backpressure Runbook

This runbook outlines the steps to handle a situation where worker queues (Redis streams) are growing faster than consumers can process them.

## Alert Triggers
- `WorkerQueueLag`

## Immediate Actions
1. **Identify the Lagging Stream**:
   Check the Grafana "Worker Queue Depth" panel to see which stream is backing up (e.g., `generation`, `export`, `delivery`, `notification`).

2. **Check Worker Logs**:
   Look for exceptions, crashes, or timeouts in the corresponding worker pods.
   ```bash
   kubectl logs -n systemforge -l app=systemforge-worker-<worker_name>
   ```

3. **Check External API Rate Limits**:
   If the lagging worker is `generation`, check if OpenAI/Anthropic APIs are returning 429 Too Many Requests or 5xx errors.
   If `notification`, check SendGrid/APNs/FCM status.

## Resolution
1. **Scale Workers**:
   If the backlog is due to a surge in legitimate traffic and no external rate limits are blocking, temporarily increase the HPA max replicas or manually scale the deployment.
   ```bash
   kubectl scale deployment -n systemforge systemforge-worker-<worker_name> --replicas=<new_count>
   ```

2. **Clear Poison Pills**:
   If a specific message is causing workers to crash continuously, it may need to be acknowledged manually and moved to a Dead Letter Queue (DLQ).
   ```bash
   kubectl exec -it <redis-pod> -- redis-cli XPENDING sf:rt:v1:stream <consumer_group>
   # Identify the ID, then:
   kubectl exec -it <redis-pod> -- redis-cli XACK sf:rt:v1:stream <consumer_group> <message_id>
   ```

3. **Pause New Requests**:
   In extreme cases, temporarily block new job creation via API gateway rules or feature flags until the queue recovers.
