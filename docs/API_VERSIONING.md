# API Versioning & Deprecation Policy

## Versioning Model
- Header: `X-API-Version`
- Compatibility: semantic versioning semantics per major line.
- Rule: additive, backward-compatible fields/endpoints are allowed within the same major version.

## Deprecation Governance
- Deprecation is announced with response headers:
  - `Deprecation`
  - `Sunset`
  - `X-API-Deprecation-Policy`
- `/api/health/api-versions` is the contract source for active/sunset status.

## Lifecycle
1. **Announce** (deprecation headers set, changelog + docs update)
2. **Dual-run** (new/old fields coexist)
3. **Sunset** (old contract removed after communicated date)

## Consumer Safety
- No silent breaking changes in an active major version.
- Any removal requires a deprecation window and published migration guidance.

