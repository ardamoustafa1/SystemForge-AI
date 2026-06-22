# Threat Model & Risk Analysis (STRIDE)

This document outlines the security posture of SystemForge AI based on the STRIDE framework.

## 🛡️ Trust Boundaries
1. **Public Internet -> Frontend / Backend Gateway**: Terminated via HTTPS/WAF.
2. **Backend Gateway -> Internal Services**: Trusted network (VPC/K8s).
3. **Backend -> Database / Redis**: Authenticated TLS connections.
4. **Backend -> LLM Provider**: Secure outbound API connections.

## 🚨 STRIDE Analysis

### Spoofing (Authentication)
- **Threat**: Attackers forging JWTs or session hijacking.
- **Mitigation**: RS256 asymmetrical JWT signatures. Strict `HttpOnly` and `Secure` cookie attributes. Replay attacks are mitigated via token rotation and jti blacklisting in Redis.

### Tampering (Integrity)
- **Threat**: Modifying payload data in transit.
- **Mitigation**: TLS 1.2+ mandatory. Content-Security-Policy (CSP) headers block malicious scripts. Database is protected by role-based access control (RBAC).

### Repudiation (Non-repudiation)
- **Threat**: Malicious actor claiming they didn't perform an action.
- **Mitigation**: Critical actions (workspace creation, design deletion) emit Audit Logs via the Outbox pattern.

### Information Disclosure (Confidentiality)
- **Threat**: Leaking proprietary design architecture or secrets.
- **Mitigation**: Row-level tenant isolation logic in SQLAlchemy queries. Hardcoded secrets are blocked by pre-commit hooks and GitHub Advanced Security.

### Denial of Service (Availability)
- **Threat**: Brute-force attacks or massive LLM prompt injection causing resource starvation.
- **Mitigation**: Multi-tier rate limiting via Redis. LLM Prompt Abuse Policy is set to `challenge` or `block`. Kubernetes HPA auto-scales pods based on CPU utilization.

### Elevation of Privilege (Authorization)
- **Threat**: Viewer attempting to mutate a design or access admin settings.
- **Mitigation**: Strict Pydantic-based endpoint RBAC. `WorkspaceMember` roles (Admin, Editor, Viewer) are checked on every mutating request.
