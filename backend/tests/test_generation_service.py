import pytest
from unittest.mock import patch
from app.services.generation_service import generate_structured_design
from app.schemas.design import DesignInputPayload, DesignOutputPayload

@pytest.mark.asyncio
@patch("app.services.generation_service.create_structured_response")
async def test_generate_structured_design_success(mock_create):
    mock_create.return_value = (
        '{"architecture": [], "data_models": [], "api_endpoints": [], "estimated_cloud_cost": {}, "engineering_checklist": []}',
        100
    )
    input_payload = DesignInputPayload(
        project_title="Test App",
        project_type="web",
        problem_statement="This is a long enough problem statement for the test to pass.",
        expected_users="100",
        traffic_assumptions="test",
        budget_sensitivity="low",
        preferred_stack="test",
        constraints="test",
        deployment_scope="global",
        data_sensitivity="low",
        real_time_required=False,
        mode="product"
    )
    with patch("app.services.generation_service.get_settings") as mock_settings, \
         patch("app.services.generation_service.parse_structured_output") as mock_parse, \
         patch("app.services.generation_service.finalize_design_output") as mock_finalize:
        mock_settings.return_value.openai_api_key = "test_key"
        mock_settings.return_value.openai_model = "test-model"
        
        mock_output = DesignOutputPayload.model_construct(architecture=[])
        mock_parse.return_value = mock_output
        mock_finalize.return_value = mock_output
        
        output, elapsed, model = await generate_structured_design(input_payload)
        
        assert model == "test-model"
        assert getattr(output, "runtime_topology", None) is not None

@pytest.mark.asyncio
async def test_generate_structured_design_fallback():
    input_payload = DesignInputPayload(
        project_title="Test App",
        project_type="web",
        problem_statement="This is a long enough problem statement for the test to pass.",
        expected_users="100",
        traffic_assumptions="test",
        budget_sensitivity="low",
        preferred_stack="test",
        constraints="test",
        deployment_scope="global",
        data_sensitivity="low",
        real_time_required=False,
        mode="product"
    )
    with patch("app.services.generation_service.get_settings") as mock_settings:
        mock_settings.return_value.openai_api_key = ""
        output, elapsed, model = await generate_structured_design(input_payload)
        
        assert model == "fallback-no-api-key"
