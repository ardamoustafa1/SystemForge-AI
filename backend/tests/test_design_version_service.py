import pytest
from tests.test_api_flows import register_and_login, create_design

def test_design_version_service_endpoints(client):
    headers = register_and_login(client, "versiontest@example.com")
    
    # Create design
    created = create_design(client, headers=headers, title="Version 1 Design")
    assert created.status_code == 200
    design_id = created.json()["id"]
    
    # List versions
    vers = client.get(f"/api/designs/{design_id}/versions", headers=headers)
    assert vers.status_code == 200
    versions = vers.json()
    assert len(versions) >= 1
    
    v1_id = versions[-1]["id"]
    
    # Regenerate to create version 2
    regen = client.post(f"/api/designs/{design_id}/regenerate", headers=headers)
    assert regen.status_code == 202
    
    vers2 = client.get(f"/api/designs/{design_id}/versions", headers=headers)
    assert vers2.status_code == 200
    versions2 = vers2.json()
    assert len(versions2) > len(versions)
    
    v2_id = versions2[-1]["id"]
    
    # Get specific version detail
    v_detail = client.get(f"/api/designs/{design_id}/versions/{v1_id}", headers=headers)
    assert v_detail.status_code == 200
    assert "core_components" in v_detail.json()["output"]
    
    # Compare versions
    comp = client.get(f"/api/designs/{design_id}/versions/compare?a={v1_id}&b={v2_id}", headers=headers)
    assert comp.status_code == 200
    
    # Explain versions
    explain = client.get(f"/api/designs/{design_id}/versions/explain?a={v1_id}&b={v2_id}", headers=headers)
    assert explain.status_code == 200
