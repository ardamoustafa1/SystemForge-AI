# ADR-001: Workspace-First Authorization

## Status
Accepted

## Context
Design, export, and version endpoints had mixed ownership logic (`owner_id` and workspace role checks), creating inconsistent access semantics.

## Decision
Adopt workspace-first authorization for design artifacts:
- Active workspace is resolved from `X-Workspace-Id` or user default workspace.
- Access checks use `WorkspaceMember.role`.
- Policy helpers centralize write/share restrictions.

## Consequences
- Consistent authorization behavior across design surfaces.
- Better support for collaborative teams.
- Fewer authorization regressions through shared policy helpers.
