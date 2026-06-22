# Maintainer Guide

This guide keeps the project coherent as it grows.

## Project Principles

1. Artifact-first beats chat-first.
2. Schema validity is a product feature.
3. Workspace authorization boundaries are non-negotiable.
4. Demo experience must stay fast and honest.
5. Production-oriented does not mean overclaiming production readiness.

## Review Checklist

For every PR, check:

- Does the change preserve workspace isolation?
- Are API contracts and schemas updated?
- Are tests proportionate to the risk?
- Are docs updated if the user/developer workflow changed?
- Are secrets, tokens, and generated local artifacts excluded?
- Is the README still truthful?

## Labeling

Recommended labels:

- `good first issue`
- `help wanted`
- `area:frontend`
- `area:backend`
- `area:ops`
- `area:docs`
- `security`
- `breaking-change`

## Release Hygiene

- Keep `CHANGELOG.md` current.
- Prefer small releases over giant surprise releases.
- Tag only after CI is green.
- Document known limitations instead of hiding them.

## Demo Hygiene

Before public sharing:

- Run the 3-minute demo script.
- Verify screenshots in `docs/assets`.
- Confirm demo credentials work locally.
- Confirm README claims match the current product state.
