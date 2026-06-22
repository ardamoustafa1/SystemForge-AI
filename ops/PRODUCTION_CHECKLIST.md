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
- Ensure `cert-manager` is installed on your cluster.
- The NGINX Ingress controller will inject strict security headers (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Strict-Transport-Security`).
- Ensure `CORS_ORIGINS` are locked to your specific frontend URL.
