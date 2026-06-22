import pytest
from tests.test_api_flows import register_and_login


def setup_workspace_with_roles(client):
    admin_headers = register_and_login(client, "rbac-admin@example.com")
    me = client.get("/api/auth/me", headers=admin_headers)
    assert me.status_code == 200
    workspace_id = me.json()["default_workspace_id"]
    admin_headers["X-Workspace-Id"] = str(workspace_id)

    # invite editor
    client.cookies.clear()
    register_and_login(client, "rbac-editor@example.com")
    client.cookies.clear()
    login_admin = client.post("/api/auth/login", json={"email": "rbac-admin@example.com", "password": "StrongPass1"})
    admin_headers["x-csrf-token"] = login_admin.cookies.get("sf_csrf_token")
    client.post(
        f"/api/workspaces/{workspace_id}/members",
        json={"email": "rbac-editor@example.com", "role": "editor"},
        headers=admin_headers,
    )

    # invite viewer
    client.cookies.clear()
    register_and_login(client, "rbac-viewer@example.com")
    client.cookies.clear()
    login_admin = client.post("/api/auth/login", json={"email": "rbac-admin@example.com", "password": "StrongPass1"})
    admin_headers["x-csrf-token"] = login_admin.cookies.get("sf_csrf_token")
    client.post(
        f"/api/workspaces/{workspace_id}/members",
        json={"email": "rbac-viewer@example.com", "role": "viewer"},
        headers=admin_headers,
    )

    # login editor and viewer to get headers
    client.cookies.clear()
    login_editor = client.post("/api/auth/login", json={"email": "rbac-editor@example.com", "password": "StrongPass1"})
    editor_headers = {"x-csrf-token": login_editor.cookies.get("sf_csrf_token"), "X-Workspace-Id": str(workspace_id)}

    client.cookies.clear()
    login_viewer = client.post("/api/auth/login", json={"email": "rbac-viewer@example.com", "password": "StrongPass1"})
    viewer_headers = {"x-csrf-token": login_viewer.cookies.get("sf_csrf_token"), "X-Workspace-Id": str(workspace_id)}

    # create a design for testing
    client.cookies.clear()
    login_admin = client.post("/api/auth/login", json={"email": "rbac-admin@example.com", "password": "StrongPass1"})
    admin_headers["x-csrf-token"] = login_admin.cookies.get("sf_csrf_token")

    design_payload = {
        "input": {
            "project_title": "RBAC Test Design",
            "project_type": "web",
            "problem_statement": "Testing workspace RBAC boundaries",
            "expected_users": "100",
            "traffic_assumptions": "low",
            "budget_sensitivity": "low",
            "preferred_stack": "fastapi",
            "constraints": "none",
            "deployment_scope": "single-region",
            "data_sensitivity": "low",
            "real_time_required": False,
            "mode": "product",
        }
    }
    created = client.post("/api/designs", json=design_payload, headers=admin_headers)
    assert created.status_code == 200
    design_id = created.json()["id"]

    return {
        "admin_headers": admin_headers,
        "editor_headers": editor_headers,
        "viewer_headers": viewer_headers,
        "design_id": design_id,
        "workspace_id": workspace_id,
    }


# Matrix data
# Role, method, url_template, expected_status
MUTATIONS = [
    # Viewer should be blocked (403), Editor/Admin should be allowed (200, 202, etc.)
    ("admin", "POST", "/api/designs", 200),
    ("editor", "POST", "/api/designs", 200),
    ("viewer", "POST", "/api/designs", 403),
    ("admin", "DELETE", "/api/designs/{design_id}", 200),
    ("editor", "DELETE", "/api/designs/{design_id}", 200),
    ("viewer", "DELETE", "/api/designs/{design_id}", 403),
    ("viewer", "POST", "/api/designs/{design_id}/regenerate", 403),
    ("viewer", "PATCH", "/api/designs/{design_id}/notes", 403),
    ("viewer", "POST", "/api/designs/{design_id}/comments", 403),
    ("viewer", "POST", "/api/designs/{design_id}/share", 403),
]


@pytest.fixture
def rbac_env(client):
    return setup_workspace_with_roles(client)


@pytest.mark.parametrize("role, method, url_template, expected_status", MUTATIONS)
def test_rbac_matrix_mutations(client, rbac_env, role, method, url_template, expected_status):
    headers = rbac_env[f"{role}_headers"]
    design_id = rbac_env["design_id"]

    url = url_template.format(design_id=design_id)

    # We need to relogin to set the right cookies for the client session
    client.cookies.clear()
    login = client.post("/api/auth/login", json={"email": f"rbac-{role}@example.com", "password": "StrongPass1"})
    headers["x-csrf-token"] = login.cookies.get("sf_csrf_token")

    if method == "POST":
        if url_template == "/api/designs":
            # We are creating a new design
            payload = {
                "input": {
                    "project_title": f"{role} Design",
                    "project_type": "web",
                    "problem_statement": "Testing schema requirement",
                    "expected_users": "100",
                    "traffic_assumptions": "low",
                    "budget_sensitivity": "low",
                    "constraints": "none",
                    "deployment_scope": "single-region",
                    "data_sensitivity": "low",
                    "real_time_required": False,
                    "mode": "product",
                }
            }
            resp = client.post(url, json=payload, headers=headers)
        elif "/comments" in url:
            resp = client.post(url, json={"content": "A comment"}, headers=headers)
        elif "/regenerate" in url:
            resp = client.post(url, headers=headers)
        elif "/share" in url:
            resp = client.post(url, headers=headers)
        else:
            resp = client.post(url, headers=headers)
    elif method == "DELETE":
        resp = client.delete(url, headers=headers)
    elif method == "PATCH":
        if "/notes" in url:
            resp = client.patch(url, json={"notes": "new notes"}, headers=headers)
        else:
            resp = client.patch(url, headers=headers)

    assert resp.status_code == expected_status, resp.text
