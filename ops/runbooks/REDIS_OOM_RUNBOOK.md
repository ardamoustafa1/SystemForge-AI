# Redis OOM & Eviction Runbook

Redis acts as the core pub/sub for WebSockets, caching layer, and transactional outbox stream broker. An OOM (Out Of Memory) or high eviction rate can cause delayed worker processing or disconnected WebSockets.

## Alert Triggers
- `RedisOOM`
- `RedisHighMemoryUsage`
- `RedisEvictionRateHigh`

## Immediate Actions
1. **Check Redis Memory**:
   ```bash
   kubectl exec -it <redis-pod> -- redis-cli info memory
   ```

2. **Identify Memory Hogs**:
   ```bash
   kubectl exec -it <redis-pod> -- redis-cli --bigkeys
   ```

3. **Check Stream Lengths**:
   The primary source of unbounded memory growth is unacknowledged stream messages.
   ```bash
   kubectl exec -it <redis-pod> -- redis-cli xinfo stream sf:rt:v1:stream
   ```

## Resolution
1. **Trim Streams**:
   If consumer groups are lagging permanently or dead, trim the stream manually:
   ```bash
   kubectl exec -it <redis-pod> -- redis-cli XTRIM sf:rt:v1:stream MAXLEN 100000
   ```

2. **Scale Up**:
   If legitimate traffic is causing OOM, increase Redis memory limits in `values.yaml` and redeploy.

3. **Check Workers**:
   Ensure all workers (`generation`, `delivery`, `export`, `notification`) are running and actively acknowledging messages.
