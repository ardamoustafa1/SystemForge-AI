# Database Failover Runbook

This runbook outlines the steps to handle a PostgreSQL database failover or severe degradation.

## Alert Triggers
- `DatabaseConnectionsHigh`
- `DatabaseLatencyHigh`
- `DatabaseDown`

## Immediate Actions
1. **Verify the Issue**:
   Check the Grafana "SystemForge SLOs & Operations" dashboard to confirm that the API is seeing a high error rate related to DB connections.
   ```bash
   kubectl get pods -n systemforge -l app=systemforge-postgres
   kubectl logs -n systemforge -l app=systemforge-postgres
   ```

2. **Check Current Connections**:
   Log into the primary DB (if accessible) and check active queries.
   ```sql
   SELECT pid, age(clock_timestamp(), query_start), usename, query 
   FROM pg_stat_activity 
   WHERE query != '<IDLE>' AND query NOT ILIKE '%pg_stat_activity%' 
   ORDER BY query_start desc;
   ```

3. **Kill Stuck Connections**:
   If there is a blocked query causing issues:
   ```sql
   SELECT pg_terminate_backend(pid);
   ```

## Failover Procedure (If using managed PostgreSQL or Patroni)
1. If using AWS RDS or similar, trigger a manual failover via the cloud console.
2. If using Patroni in Kubernetes:
   ```bash
   kubectl exec -it <patroni-pod> -- patronictl failover
   ```

## Post-Mortem Actions
- Analyze slow query logs.
- Adjust connection pool settings in `values.yaml` if needed.
- Add missing indexes.
