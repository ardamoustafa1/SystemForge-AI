from app.services.export_service import build_pdf_bytes
from app.services.terraform_service import build_terraform_zip
from app.schemas.design import DesignInputPayload
from app.llm.fallback import build_fallback_output


def test_build_terraform_zip_postgres():
    design_in = DesignInputPayload(
        project_title="Test App",
        project_type="web",
        problem_statement="A web application that needs to handle 100 users",
        expected_users="100",
        traffic_assumptions="low",
        budget_sensitivity="high",
        preferred_stack="postgres",
        constraints="none",
        deployment_scope="single-region",
        data_sensitivity="low",
        real_time_required=False,
        mode="product",
    )
    design_out = build_fallback_output(design_in)

    zip_bytes = build_terraform_zip("Test App", design_in, design_out)
    assert isinstance(zip_bytes, bytes)
    assert len(zip_bytes) > 0


def test_build_pdf_bytes():
    design_in = DesignInputPayload(
        project_title="Test App",
        project_type="web",
        problem_statement="A web application that needs to handle 100 users",
        expected_users="100",
        traffic_assumptions="low",
        budget_sensitivity="high",
        preferred_stack="fastapi",
        constraints="none",
        deployment_scope="single-region",
        data_sensitivity="low",
        real_time_required=False,
        mode="product",
    )
    design_out = build_fallback_output(design_in)

    pdf_bytes = build_pdf_bytes("Test App", design_in, design_out)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")
