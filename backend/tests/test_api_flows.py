def register_and_login(client, email: str):
    register_payload = {
        "email": email,
        "full_name": "Test User",
        "password": "StrongPass1",
    }
    r = client.post("/api/auth/register", json=register_payload)
    assert r.status_code == 201

    l = client.post("/api/auth/login", json={"email": email, "password": "StrongPass1"})
    assert l.status_code == 200
    csrf = l.cookies.get("sf_csrf_token")
    assert csrf
    return {"x-csrf-token": csrf}


def create_design(client, headers: dict[str, str], title: str = "Design A"):
    payload = {
        "input": {
            "project_title": title,
            "project_type": "chat",
            "problem_statement": "Build a scalable chat backend with strong reliability guarantees.",
            "expected_users": "100000",
            "traffic_assumptions": "peak 1000 rps",
            "budget_sensitivity": "medium",
            "preferred_stack": "fastapi,postgres,redis",
            "constraints": "small team and fast launch timeline",
            "deployment_scope": "single-region",
            "data_sensitivity": "medium",
            "real_time_required": True,
            "mode": "product",
        }
    }
    return client.post("/api/designs", json=payload, headers=headers)


def test_register_login_me_and_protection(client):
    me = client.get("/api/auth/me")
    assert me.status_code == 401

    headers = register_and_login(client, "user1@example.com")
    me2 = client.get("/api/auth/me")
    assert me2.status_code == 200
    assert me2.json()["email"] == "user1@example.com"

    d = create_design(client, headers=headers)
    assert d.status_code == 200


def test_logout_revokes_active_session(client):
    headers = register_and_login(client, "revoke@example.com")
    me_before = client.get("/api/auth/me")
    assert me_before.status_code == 200

    logout_resp = client.post("/api/auth/logout", headers=headers)
    assert logout_resp.status_code == 200

    me_after = client.get("/api/auth/me")
    assert me_after.status_code == 401


def test_public_share_responses_have_security_headers(client):
    r = client.get("/api/public/share/definitely-not-a-valid-token-12345")
    assert r.status_code == 404
    assert "no-store" in (r.headers.get("cache-control") or "").lower()
    assert r.headers.get("x-api-version") == "v1"


def test_design_ownership_denial(client):
    owner_headers = register_and_login(client, "owner@example.com")
    created = create_design(client, headers=owner_headers, title="Owner Design")
    design_id = created.json()["id"]

    # new user session
    client.cookies.clear()
    other_headers = register_and_login(client, "other@example.com")
    denied = client.get(f"/api/designs/{design_id}")
    assert denied.status_code == 404

    denied_delete = client.delete(f"/api/designs/{design_id}", headers=other_headers)
    assert denied_delete.status_code == 404


def test_design_crud_export_notes_and_regenerate(client):
    headers = register_and_login(client, "flow@example.com")

    created = create_design(client, headers=headers, title="Flow Design")
    assert created.status_code == 200
    body = created.json()
    design_id = body["id"]

    listed = client.get("/api/designs")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == design_id

    detail = client.get(f"/api/designs/{design_id}")
    assert detail.status_code == 200
    assert detail.json()["title"] == "Flow Design"

    notes = client.patch(f"/api/designs/{design_id}/notes", json={"notes": "Persisted note"}, headers=headers)
    assert notes.status_code == 200
    assert notes.json()["notes"] == "Persisted note"

    export_resp = client.get(f"/api/designs/{design_id}/export?format=markdown")
    assert export_resp.status_code == 200
    assert "content" in export_resp.json()

    regen = client.post(f"/api/designs/{design_id}/regenerate", headers=headers)
    assert regen.status_code == 202
    assert regen.json()["status"] == "completed"

    deleted = client.delete(f"/api/designs/{design_id}", headers=headers)
    assert deleted.status_code == 200


def test_initial_version_snapshot_and_share_flow(client):
    headers = register_and_login(client, "shareflow@example.com")
    created = create_design(client, headers=headers, title="İlk Türkçe Başlık")
    assert created.status_code == 200
    design_id = created.json()["id"]

    vers = client.get(f"/api/designs/{design_id}/versions", headers=headers)
    assert vers.status_code == 200
    assert len(vers.json()) >= 1

    regen = client.post(f"/api/designs/{design_id}/regenerate", headers=headers)
    assert regen.status_code == 202
    vers2 = client.get(f"/api/designs/{design_id}/versions", headers=headers)
    assert vers2.status_code == 200
    assert len(vers2.json()) >= 1

    en = client.post(f"/api/designs/{design_id}/share", headers=headers)
    assert en.status_code == 200
    body = en.json()
    assert body["enabled"] is True
    assert body["share_url"]
    token = body["share_url"].split("/share/")[-1]

    pub = client.get(f"/api/public/share/{token}")
    assert pub.status_code == 200
    assert pub.json()["title"] == "İlk Türkçe Başlık"

    pdf = client.get(f"/api/public/share/{token}/export?format=pdf")
    assert pdf.status_code == 200
    assert pdf.content[:4] == b"%PDF"
    assert len(pdf.content) > 500

    dis = client.delete(f"/api/designs/{design_id}/share", headers=headers)
    assert dis.status_code == 200
    assert client.get(f"/api/public/share/{token}").status_code == 404


def test_authz_contract_matrix_roles_vs_design_actions(client):
    admin_headers = register_and_login(client, "matrix-admin@example.com")
    admin_me = client.get("/api/auth/me")
    assert admin_me.status_code == 200
    workspace_id = admin_me.json()["default_workspace_id"]
    admin_headers["X-Workspace-Id"] = str(workspace_id)
    created = create_design(client, headers=admin_headers, title="Matrix Design")
    assert created.status_code == 200
    design_id = created.json()["id"]

    # Editor member
    client.cookies.clear()
    editor_headers = register_and_login(client, "matrix-editor@example.com")
    editor_headers["X-Workspace-Id"] = str(workspace_id)
    client.cookies.clear()
    login_admin = client.post("/api/auth/login", json={"email": "matrix-admin@example.com", "password": "StrongPass1"})
    assert login_admin.status_code == 200
    admin_headers = {"x-csrf-token": login_admin.cookies.get("sf_csrf_token"), "X-Workspace-Id": str(workspace_id)}
    invite_editor = client.post(
        f"/api/workspaces/{workspace_id}/members",
        json={"email": "matrix-editor@example.com", "role": "editor"},
        headers=admin_headers,
    )
    assert invite_editor.status_code in {200, 201}

    # Viewer member
    client.cookies.clear()
    viewer_headers = register_and_login(client, "matrix-viewer@example.com")
    viewer_headers["X-Workspace-Id"] = str(workspace_id)
    client.cookies.clear()
    login_admin = client.post("/api/auth/login", json={"email": "matrix-admin@example.com", "password": "StrongPass1"})
    assert login_admin.status_code == 200
    admin_headers = {"x-csrf-token": login_admin.cookies.get("sf_csrf_token"), "X-Workspace-Id": str(workspace_id)}
    invite_viewer = client.post(
        f"/api/workspaces/{workspace_id}/members",
        json={"email": "matrix-viewer@example.com", "role": "viewer"},
        headers=admin_headers,
    )
    assert invite_viewer.status_code in {200, 201}

    # Editor can update notes
    client.cookies.clear()
    editor_login = client.post("/api/auth/login", json={"email": "matrix-editor@example.com", "password": "StrongPass1"})
    assert editor_login.status_code == 200
    editor_headers = {"x-csrf-token": editor_login.cookies.get("sf_csrf_token"), "X-Workspace-Id": str(workspace_id)}
    editor_note = client.patch(f"/api/designs/{design_id}/notes", json={"notes": "editor-note"}, headers=editor_headers)
    assert editor_note.status_code == 200

    # Viewer can read but cannot mutate
    client.cookies.clear()
    viewer_login = client.post("/api/auth/login", json={"email": "matrix-viewer@example.com", "password": "StrongPass1"})
    assert viewer_login.status_code == 200
    viewer_headers = {"x-csrf-token": viewer_login.cookies.get("sf_csrf_token"), "X-Workspace-Id": str(workspace_id)}
    viewer_get = client.get(f"/api/designs/{design_id}", headers=viewer_headers)
    assert viewer_get.status_code == 200
    viewer_note = client.patch(f"/api/designs/{design_id}/notes", json={"notes": "viewer-note"}, headers=viewer_headers)
    assert viewer_note.status_code == 403
    viewer_share = client.post(f"/api/designs/{design_id}/share", headers=viewer_headers)
    assert viewer_share.status_code == 403
