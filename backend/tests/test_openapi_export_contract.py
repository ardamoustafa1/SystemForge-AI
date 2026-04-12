"""OpenAPI documents dual content-types for export endpoints (JSON vs PDF)."""


def test_export_paths_document_both_media_types(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    paths = spec.get("paths", {})

    auth_export = paths.get("/api/designs/{design_id}/export", {}).get("get", {})
    pub_export = paths.get("/api/public/share/{token}/export", {}).get("get", {})

    for name, op in [("auth", auth_export), ("public", pub_export)]:
        content = op.get("responses", {}).get("200", {}).get("content", {})
        assert "application/json" in content, f"{name} missing application/json"
        assert "application/pdf" in content, f"{name} missing application/pdf"
        assert "#/components/schemas/ExportResponse" in str(content["application/json"]), name
