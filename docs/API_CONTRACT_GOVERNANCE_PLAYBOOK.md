# API Contract Governance Playbook

## Versioning
- Version header: `X-API-Version`
- Major versions define compatibility boundary.
- Minor changes must remain backward-compatible.

## Deprecation Workflow
1. Announce using headers:
   - `Deprecation`
   - `Sunset`
   - `X-API-Deprecation-Policy`
2. Publish migration guidance.
3. Keep dual contract window until sunset date.
4. Remove deprecated fields/routes after sunset.

## Test Governance
- Contract tests for role/endpoint/action matrix.
- Schema compatibility checks for core responses.
- Public/share endpoints must preserve no-store/security headers.

## Operational Controls
- `/api/health/api-versions` is source of truth.
- CI gate blocks breaking changes without version bump/deprecation notes.

