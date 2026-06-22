# SystemForge API Reference

Welcome to the SystemForge API. Our API is organized around REST. Our API has predictable resource-oriented URLs, returns JSON-encoded responses, and uses standard HTTP response codes, authentication, and verbs.

## Base URL
```
http://localhost:8000/api
```

## Authentication
Authentication to the API is performed via HTTP-Only Cookies for web clients or API Keys via `Authorization: Bearer <token>` for programmatic access.

## Endpoints

### 1. Designs
- `GET /api/designs` - List all designs in your workspace.
- `POST /api/designs` - Create a new design generation request.
- `GET /api/designs/{id}` - Retrieve details of a specific design.
- `DELETE /api/designs/{id}` - Delete a design.

### 2. Workspaces
- `GET /api/workspaces` - List your workspaces.
- `POST /api/workspaces` - Create a new workspace.
- `GET /api/workspaces/{id}/members` - List workspace members.

### 3. Authentication
- `GET /api/auth/me` - Get current user info.
- `POST /api/auth/api-keys` - Generate an API key.
