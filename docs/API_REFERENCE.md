# SystemForge API Reference

Welcome to the SystemForge API. Our API is organized around REST, returns JSON-encoded responses, and uses standard HTTP response codes.

## Base URL
`http://localhost:8000/api`

## Authentication
Authentication is performed via `Authorization: Bearer <token>`. You can obtain a token by signing in.

---

## 1. Designs

### Create a Design
`POST /api/designs`

Creates a new architecture design request. This operation is asynchronous.

**Request Body:**
```json
{
  "project_title": "E-commerce Platform",
  "project_category": "Retail",
  "business_requirements": "Must handle 10k RPS during sales."
}
```

**Response (202 Accepted):**
```json
{
  "id": 101,
  "status": "pending",
  "project_title": "E-commerce Platform",
  "created_at": "2026-06-22T10:00:00Z"
}
```

### Get a Design
`GET /api/designs/{id}`

Retrieves the current state of a design. If `status` is `approved`, the `output` field will contain the full architecture payload.

---

## 2. Workspaces

### List Workspaces
`GET /api/workspaces`

Returns a list of workspaces the authenticated user belongs to.

**Response (200 OK):**
```json
{
  "workspaces": [
    {
      "id": 1,
      "name": "Acme Corp Engineering",
      "role": "admin"
    }
  ]
}
```

---

## 3. WebSockets

### Realtime Updates
`WS /api/ws/designs/{id}`

Establish a WebSocket connection to receive live updates.

**Incoming Messages (from Server):**
```json
{
  "type": "design_updated",
  "payload": {
    "status": "generating",
    "progress": 45
  }
}
```

## Error Codes

| Status Code | Description |
|---|---|
| `400 Bad Request` | Invalid parameters or malformed JSON. |
| `401 Unauthorized` | Missing or invalid Bearer token. |
| `403 Forbidden` | User lacks permission (RBAC violation). |
| `404 Not Found` | Resource does not exist. |
| `429 Too Many Requests` | Rate limit exceeded. |
| `500 Internal Error` | Unexpected backend failure. |
