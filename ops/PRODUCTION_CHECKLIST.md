# Production Readiness & Security Checklist

This document details the required infrastructure changes to deploy SystemForge AI safely into a production Kubernetes environment.

## 1. Secrets Management
**DO NOT** commit plaintext secrets (`JWT_SECRET`, `OPENAI_API_KEY`, DB Passwords) to version control.
You must use a Secrets Operator. Recommended choices:

- **ExternalSecrets Operator**: Pulls secrets directly from AWS Secrets Manager, Google Secret Manager, or HashiCorp Vault.
- **SOPS / SealedSecrets**: Encrypts Kubernetes Secrets inside the Git repository using a master KMS key.

*Usage Example:* Replace the Helm `--set env.jwtSecret=...` with a pre-created Kubernetes Secret synced by the operator.

## 2. Production Database & PITR
The internal PostgreSQL database deployed via `postgres.yaml` is for **Demo, Staging, and Development only**.
For Production:
- Disable the internal DB: `helm install systemforge . --set postgres.enabled=false`
- Use a Managed Database Provider (AWS RDS, Google Cloud SQL, or Azure Database for PostgreSQL).
- **Point-In-Time Recovery (PITR)**: Ensure PITR is enabled on the managed database with at least a 7-day retention period.
- Set the `DATABASE_URL` securely via your Secrets Management tool.

## 3. Kubernetes Migration Hooks
The `migration-job.yaml` is configured with an `initContainer` that uses `pg_isready` to poll the database before applying migrations. This prevents the hook from failing prematurely while the cluster database initializes. In production managed databases, this ensures seamless deployment pipelines even during network latency.

## 4. Ingress, TLS, & Security Headers
The Helm chart is configured by default to utilize `cert-manager.io/cluster-issuer: "letsencrypt-prod"`.
- **Domain configuration:** `systemforge.local` is used as a placeholder in `values.yaml`. You MUST override this with your actual production domain (e.g., `app.yourcompany.com`) during deployment.
- Ensure `cert-manager` is installed on your cluster.
- The NGINX Ingress controller will inject strict security headers (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Strict-Transport-Security`).
- Ensure `CORS_ORIGINS` are locked to your specific frontend URL.

## 5. Web Application Firewall (WAF) & Rate Limiting
For enterprise deployments, protect your Ingress controller with a WAF (e.g., AWS WAF, Cloudflare, or Azure Front Door).
- Configure rules to block common OWASP Top 10 vulnerabilities (SQLi, XSS).
- The application includes an internal Redis-backed rate limiter, but edge-level rate limiting is strongly recommended to protect against volumetric DDoS attacks.

## 6. Observability (Monitoring & Alerting)
SystemForge AI is instrumented with OpenTelemetry.
- Deploy an APM tool (Datadog, New Relic, or Prometheus/Grafana) to scrape the metrics endpoints.
- Configure alerts for:
  - Error rates exceeding 1% on generation endpoints.
  - Redis memory utilization > 80%.
  - LLM API latency or timeout spikes.

## 7. Disaster Recovery & Incident Response
Establish a clear Disaster Recovery (DR) plan:
- **Database Backups**: Verify automated daily snapshots and test restoration at least quarterly.
- **Incident Response Playbook**: Document the procedure for rotating compromised `JWT_SECRET` and `OPENAI_API_KEY`.
- **Zero-Downtime Deployment**: The worker nodes are stateless and can be scaled independently, but ensure your database migrations are backward-compatible.
