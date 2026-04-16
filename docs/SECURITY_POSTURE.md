# Security Posture

## Implemented Controls
- CSRF double-submit validation for mutating HTTP routes
- Workspace-first authorization checks
- JWT revocation using token-version strategy
- WebSocket auth + token-version validation
- Global security response headers (CSP, XFO, nosniff, permissions policy, HSTS when secure)
- Prompt sanitization and injection redaction guards
- API and websocket abuse throttling
- Notification token log redaction

## CI Security Gates
- `pip-audit` for backend dependencies
- `npm audit` for frontend dependencies

## Next Hardening Steps
- Refresh token rotation with device-bound sessions
- Abuse analytics dashboard and anomaly alerting
- Quarterly secret-rotation exercise and key-compromise drills
