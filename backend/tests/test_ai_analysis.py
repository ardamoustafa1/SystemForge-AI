from tests.test_api_flows import register_and_login

def test_job_center(client):
    headers = register_and_login(client, "jobs@example.com")
    res = client.get("/api/dashboard/job-center", headers=headers)
    assert res.status_code == 200
    assert "jobs" in res.json()

def test_pricing_view(client):
    headers = register_and_login(client, "pricing@example.com")
    res = client.get("/api/cost/pricing", headers=headers)
    assert res.status_code == 200

def test_usage_view(client):
    headers = register_and_login(client, "usage@example.com")
    me = client.get("/api/auth/me", headers=headers)
    workspace_id = me.json()["default_workspace_id"]
    headers["X-Workspace-Id"] = str(workspace_id)
    
    res = client.get(f"/api/workspaces/{workspace_id}/cost/usage", headers=headers)
    assert res.status_code == 200

def test_template_policy(client):
    headers = register_and_login(client, "policy@example.com")
    me = client.get("/api/auth/me", headers=headers)
    workspace_id = me.json()["default_workspace_id"]
    headers["X-Workspace-Id"] = str(workspace_id)
    
    res = client.get(f"/api/workspaces/{workspace_id}/templates-policy", headers=headers)
    assert res.status_code == 200
