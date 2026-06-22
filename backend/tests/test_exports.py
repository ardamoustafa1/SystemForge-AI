import pytest
from unittest.mock import MagicMock
import zipfile
import io

from app.services.export_service import build_markdown_export
from app.services.terraform_service import build_terraform_zip
from app.schemas.design import DesignInputPayload


@pytest.fixture
def mock_design_input():
    return DesignInputPayload(
        project_title="Test Project",
        project_type="web",
        problem_statement="This is a long enough problem statement for the test to pass.",
        expected_users="10k",
        traffic_assumptions="test",
        budget_sensitivity="high",
        preferred_stack="react, python, postgres",
        constraints="test",
        deployment_scope="global",
        data_sensitivity="low",
        real_time_required=False,
        mode="product"
    )


@pytest.fixture
def mock_design_output():
    output = MagicMock()
    # Fill in required properties for markdown export
    output.executive_summary = "This is a test summary."
    output.high_level_architecture = "High level arch."
    output.runtime_topology.architecture_style = "Microservices"
    output.runtime_topology.deployable_units = ["api", "worker"]
    output.runtime_topology.primary_runtime_paths = []
    output.runtime_topology.stateful_components = []
    output.data_flows.request_response_flow = []
    output.data_flows.asynchronous_event_flow = []
    output.data_flows.persistence_flow = []
    output.data_flows.failure_recovery_flow = []
    output.websocket_architecture.connection_lifecycle = []
    output.websocket_architecture.fanout_strategy = []
    output.websocket_architecture.scaling_strategy = []
    output.websocket_architecture.channel_partitioning = []
    output.websocket_architecture.shard_strategy = []
    output.websocket_architecture.topic_design = []
    output.websocket_architecture.partition_keys = []
    output.websocket_architecture.pubsub_backplane = ""
    output.websocket_architecture.sticky_session_strategy = ""
    output.video_streaming_architecture.streaming_protocols = []
    output.video_streaming_architecture.ingest_and_packaging = []
    output.video_streaming_architecture.cdn_strategy = []
    output.video_streaming_architecture.adaptive_bitrate_strategy = []
    output.video_streaming_architecture.realtime_interaction_sidecar = []
    output.database_architecture.primary_entities = []
    output.database_architecture.schema_design = []
    output.database_architecture.indexing_strategy = []
    output.database_architecture.partitioning_strategy = []
    output.database_architecture.consistency_and_migration_notes = []
    output.observability_architecture.logging_strategy = []
    output.observability_architecture.tracing_strategy = []
    output.observability_architecture.metrics_strategy = []
    output.observability_architecture.alerting_strategy = []
    output.observability_architecture.sli_slo_targets = []
    output.ai_architecture.request_guardrails = []
    output.ai_architecture.inference_orchestration = []
    output.ai_architecture.queue_and_backpressure = []
    output.ai_architecture.model_provider_strategy = []
    output.ai_architecture.fallback_and_recovery = []
    output.queue_event_strategy = ""
    output.security_architecture.auth_flow = []
    output.security_architecture.session_and_refresh_flow = []
    output.security_architecture.abuse_protection = []
    output.security_architecture.secrets_and_key_management = []
    output.security_architecture.audit_and_compliance = []
    output.security_considerations = []
    output.assumptions = []
    output.architecture_decisions = []
    output.open_questions = []
    output.consistency_warnings = []
    output.functional_requirements = []
    output.non_functional_requirements = []
    output.core_components = ["postgres", "redis"]
    output.scalability_plan = []
    output.reliability_and_failure_points = []
    output.cost_considerations = []
    output.tradeoff_decisions = []
    
    scorecard = MagicMock()
    scorecard.scalability = 8
    scorecard.reliability = 7
    scorecard.security = 8
    scorecard.maintainability = 8
    scorecard.cost_efficiency = 8
    scorecard.simplicity = 7
    scorecard.biggest_risk = "None"
    scorecard.biggest_bottleneck = "DB"
    scorecard.first_optimization = "Cache"
    scorecard.avoid_overengineering = "Keep it simple"
    output.architecture_scorecard = scorecard
    
    output.recommended_implementation_phases = []
    output.engineering_checklist = ["Task 1", "Task 2"]
    output.suggested_mermaid_diagram = "graph TD; A-->B;"
    output.final_recommendation = "Ship it."
    
    return output


def test_build_markdown_export(mock_design_input, mock_design_output):
    title = "Test Project"
    md_content = build_markdown_export(title, mock_design_input, mock_design_output)
    
    # Assertions to verify the markdown structure contains the provided outputs
    assert "# Test Project" in md_content
    assert "## Executive Summary" in md_content
    assert "This is a test summary." in md_content
    assert "- [ ] Task 1" in md_content
    assert "- [ ] Task 2" in md_content
    assert "graph TD; A-->B;" in md_content
    assert "Ship it." in md_content


def test_build_terraform_zip(mock_design_input, mock_design_output):
    title = "Test Project"
    zip_bytes = build_terraform_zip(title, mock_design_input, mock_design_output)
    
    assert isinstance(zip_bytes, bytes)
    assert len(zip_bytes) > 0
    
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        file_list = zf.namelist()
        # Verify basic files are populated in the zip
        assert any("README.md" in f for f in file_list)
        assert any("main.tf" in f for f in file_list)
        assert any("variables.tf" in f for f in file_list)
        assert any("outputs.tf" in f for f in file_list)
        
        # Verify content of main.tf
        main_tf_path = next(f for f in file_list if "main.tf" in f)
        main_tf_content = zf.read(main_tf_path).decode('utf-8')
        
        # Since 'postgres' and 'redis' are in our mock core_components, they should be in the terraform module
        assert 'module "db"' in main_tf_content
        assert 'aws_elasticache_cluster' in main_tf_content
