# Authz Contract Matrix

Role x Endpoint x Action contract for workspace-scoped design operations.

## Design Surface

| Endpoint | Action | Admin | Editor | Viewer |
|---|---|---:|---:|---:|
| `GET /api/designs` | list | ✅ | ✅ | ✅ |
| `GET /api/designs/{id}` | read detail | ✅ | ✅ | ✅ |
| `POST /api/designs` | create | ✅ | ✅ | ❌ |
| `PATCH /api/designs/{id}/notes` | modify | ✅ | ✅ | ❌ |
| `POST /api/designs/{id}/regenerate` | mutate generation | ✅ | ✅ | ❌ |
| `POST /api/designs/{id}/share` | manage sharing | ✅ | ✅ | ❌ |
| `PATCH /api/designs/{id}/review` | approval workflow | ✅ | ✅ | ❌ |
| `POST /api/designs/{id}/comments` | comment thread | ✅ | ✅ | ❌ |

## Workspace Surface

| Endpoint | Action | Admin | Editor | Viewer |
|---|---|---:|---:|---:|
| `POST /api/workspaces/{id}/members` | invite | ✅ | ✅ | ❌ |
| `PATCH /api/workspaces/{id}/members/{member_id}` | role update | ✅ | ❌ | ❌ |
| `PATCH /api/workspaces/{id}/budget` | budget control | ✅ | ❌ | ❌ |
| `GET /api/security/audit-trail` | audit visibility | ✅ | ❌ | ❌ |

## Enforcement Location
- `app/auth/deps.py`
- `app/services/authorization_service.py`
- `app/services/design_service.py`
- `app/services/workspace_service.py`

