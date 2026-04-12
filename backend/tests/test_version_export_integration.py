"""Integration: version list/detail/compare and export formats."""

from tests.test_api_flows import create_design, register_and_login


def test_versions_detail_compare_and_exports(client):
    headers = register_and_login(client, "versions@example.com")
    created = create_design(client, headers=headers, title="Version API Integration")
    assert created.status_code == 200
    design_id = created.json()["id"]

    v1 = client.get(f"/api/designs/{design_id}/versions", headers=headers)
    assert v1.status_code == 200
    versions = v1.json()
    assert len(versions) >= 1
    vid = versions[0]["id"]

    detail = client.get(f"/api/designs/{design_id}/versions/{vid}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["id"] == vid
    assert "output" in detail.json()

    # Different scale stances change fallback markdown so snapshots are not skipped as duplicates.
    r1 = client.post(
        f"/api/designs/{design_id}/regenerate",
        headers=headers,
        json={"scale_stance": "aggressive"},
    )
    assert r1.status_code == 202
    r2 = client.post(
        f"/api/designs/{design_id}/regenerate",
        headers=headers,
        json={"scale_stance": "conservative"},
    )
    assert r2.status_code == 202

    versions_after = client.get(f"/api/designs/{design_id}/versions", headers=headers).json()
    assert len(versions_after) >= 2
    a, b = versions_after[0]["id"], versions_after[1]["id"]

    cmp = client.get(f"/api/designs/{design_id}/versions/compare?a={a}&b={b}", headers=headers)
    assert cmp.status_code == 200
    assert "diff_markdown" in cmp.json()

    md = client.get(f"/api/designs/{design_id}/export?format=markdown", headers=headers)
    assert md.status_code == 200
    body = md.json()
    assert body["format"] == "markdown"
    assert len(body["content"]) > 100

    pdf = client.get(f"/api/designs/{design_id}/export?format=pdf", headers=headers)
    assert pdf.status_code == 200
    assert pdf.content[:4] == b"%PDF"
    assert pdf.headers.get("content-type", "").startswith("application/pdf")
