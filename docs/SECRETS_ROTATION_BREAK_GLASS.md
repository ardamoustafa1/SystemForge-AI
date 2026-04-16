# Secrets Rotation & Break-Glass Procedure

## Rotation Policy
- Rotate JWT secret and provider credentials every 90 days (or incident-triggered).
- Use staged rollout:
  1. Introduce new secret as secondary verification key.
  2. Re-issue sessions/tokens.
  3. Promote new secret to primary signer.
  4. Remove old secret after grace period.

## Automation Hooks
- CI scheduled job triggers secret rotation checklist.
- Deployment pipeline validates:
  - `cookie_secure=true` in non-dev
  - non-default JWT secret length/entropy
  - audit trail event emission

## Break-Glass
Use only for active compromise:
1. Freeze token issuance.
2. Invalidate all sessions (`token_version` increment + refresh session revoke).
3. Rotate JWT secret and provider secrets.
4. Enable strict abuse policy mode (`block`).
5. Notify on-call + security owner and begin incident postmortem.

