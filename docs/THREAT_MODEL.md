# Threat Model (STRIDE Summary)

## Assets
- User sessions (JWT cookies)
- Design artifacts and exports
- Workspace membership/roles
- Notification device tokens

## Key Threats and Mitigations

### Spoofing
- Threat: stolen JWT token reuse.
- Mitigation: token version claim (`tv`) + revocation on logout, WS token version validation.

### Tampering
- Threat: cross-workspace access attempts.
- Mitigation: workspace-first authz dependency and centralized policy checks.

### Repudiation
- Threat: missing request/event traceability.
- Mitigation: request IDs, worker event metrics, stream event logs.

### Information Disclosure
- Threat: token leakage in logs.
- Mitigation: notification token redaction.

### Denial of Service
- Threat: WS flood and export-heavy sync workloads.
- Mitigation: websocket rate limiting, queued export jobs, rate limits and usage quotas.

### Elevation of Privilege
- Threat: role bypass on design endpoints.
- Mitigation: centralized policy layer, workspace role enforcement.
