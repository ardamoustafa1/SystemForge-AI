from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ScaleStance = Literal["balanced", "conservative", "aggressive"]


class DesignInputPayload(BaseModel):
    project_title: str = Field(min_length=3, max_length=160)
    project_type: str = Field(min_length=2, max_length=80)
    problem_statement: str = Field(min_length=20, max_length=4000)
    expected_users: str = Field(min_length=1, max_length=120)
    traffic_assumptions: str = Field(min_length=1, max_length=300)
    budget_sensitivity: Literal["low", "medium", "high"]
    preferred_stack: str | None = Field(default=None, max_length=200)
    constraints: str = Field(min_length=1, max_length=1000)
    deployment_scope: Literal["single-region", "multi-region", "global"]
    data_sensitivity: Literal["low", "medium", "high", "critical"]
    real_time_required: bool
    mode: Literal["interview", "product"]
    document_context: str | None = Field(
        default=None, 
        max_length=50000, 
        description="Raw text from uploaded PRD or design document"
    )


class Scorecard(BaseModel):
    scalability: int = Field(ge=1, le=10)
    reliability: int = Field(ge=1, le=10)
    security: int = Field(ge=1, le=10)
    maintainability: int = Field(ge=1, le=10)
    cost_efficiency: int = Field(ge=1, le=10)
    simplicity: int = Field(ge=1, le=10)
    biggest_risk: str
    biggest_bottleneck: str
    first_optimization: str
    avoid_overengineering: str
class EstimatedCloudCost(BaseModel):
    monthly_usd_min: int = Field(ge=0)
    monthly_usd_max: int = Field(ge=0)
    cost_breakdown: list[str] = Field(description="Top 3 to 5 cost drivers (e.g., EC2 instances, RDS transfer, ECS)")


class RuntimeTopologySection(BaseModel):
    architecture_style: str = ""
    deployable_units: list[str] = Field(default_factory=list)
    primary_runtime_paths: list[str] = Field(default_factory=list)
    stateful_components: list[str] = Field(default_factory=list)


class DataFlowSection(BaseModel):
    request_response_flow: list[str] = Field(default_factory=list)
    asynchronous_event_flow: list[str] = Field(default_factory=list)
    persistence_flow: list[str] = Field(default_factory=list)
    failure_recovery_flow: list[str] = Field(default_factory=list)


class WebsocketArchitectureSection(BaseModel):
    connection_lifecycle: list[str] = Field(default_factory=list)
    fanout_strategy: list[str] = Field(default_factory=list)
    scaling_strategy: list[str] = Field(default_factory=list)
    sticky_session_strategy: str = ""
    pubsub_backplane: str = ""
    channel_partitioning: list[str] = Field(default_factory=list)
    shard_strategy: list[str] = Field(default_factory=list)
    topic_design: list[str] = Field(default_factory=list)
    partition_keys: list[str] = Field(default_factory=list)


class AIArchitectureSection(BaseModel):
    request_guardrails: list[str] = Field(default_factory=list)
    inference_orchestration: list[str] = Field(default_factory=list)
    queue_and_backpressure: list[str] = Field(default_factory=list)
    model_provider_strategy: list[str] = Field(default_factory=list)
    fallback_and_recovery: list[str] = Field(default_factory=list)


class SecurityArchitectureSection(BaseModel):
    auth_flow: list[str] = Field(default_factory=list)
    session_and_refresh_flow: list[str] = Field(default_factory=list)
    abuse_protection: list[str] = Field(default_factory=list)
    secrets_and_key_management: list[str] = Field(default_factory=list)
    audit_and_compliance: list[str] = Field(default_factory=list)


class VideoStreamingArchitectureSection(BaseModel):
    streaming_protocols: list[str] = Field(default_factory=list)
    ingest_and_packaging: list[str] = Field(default_factory=list)
    cdn_strategy: list[str] = Field(default_factory=list)
    adaptive_bitrate_strategy: list[str] = Field(default_factory=list)
    realtime_interaction_sidecar: list[str] = Field(default_factory=list)


class DatabaseArchitectureSection(BaseModel):
    primary_entities: list[str] = Field(default_factory=list)
    schema_design: list[str] = Field(default_factory=list)
    indexing_strategy: list[str] = Field(default_factory=list)
    partitioning_strategy: list[str] = Field(default_factory=list)
    consistency_and_migration_notes: list[str] = Field(default_factory=list)


class ObservabilityArchitectureSection(BaseModel):
    logging_strategy: list[str] = Field(default_factory=list)
    tracing_strategy: list[str] = Field(default_factory=list)
    metrics_strategy: list[str] = Field(default_factory=list)
    alerting_strategy: list[str] = Field(default_factory=list)
    sli_slo_targets: list[str] = Field(default_factory=list)


class DesignOutputPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    executive_summary: str
    functional_requirements: list[str]
    non_functional_requirements: list[str]
    high_level_architecture: str
    core_components: list[str]
    data_layer_recommendations: list[str]
    cache_strategy: str
    queue_event_strategy: str
    api_service_design_notes: list[str]
    scalability_plan: list[str]
    reliability_and_failure_points: list[str]
    security_considerations: list[str]
    cost_considerations: list[str]
    tradeoff_decisions: list[str]
    recommended_implementation_phases: list[str]
    engineering_checklist: list[str]
    architecture_scorecard: Scorecard
    estimated_cloud_cost: EstimatedCloudCost | None = Field(
        default=None,
        description="Rough estimation of monthly cloud cost on AWS/GCP based on traffic and scale requirements."
    )
    runtime_topology: RuntimeTopologySection = Field(default_factory=RuntimeTopologySection)
    data_flows: DataFlowSection = Field(default_factory=DataFlowSection)
    websocket_architecture: WebsocketArchitectureSection = Field(default_factory=WebsocketArchitectureSection)
    ai_architecture: AIArchitectureSection = Field(default_factory=AIArchitectureSection)
    security_architecture: SecurityArchitectureSection = Field(default_factory=SecurityArchitectureSection)
    video_streaming_architecture: VideoStreamingArchitectureSection = Field(default_factory=VideoStreamingArchitectureSection)
    database_architecture: DatabaseArchitectureSection = Field(default_factory=DatabaseArchitectureSection)
    observability_architecture: ObservabilityArchitectureSection = Field(default_factory=ObservabilityArchitectureSection)
    suggested_mermaid_diagram: str
    final_recommendation: str
    assumptions: list[str] = Field(default_factory=list)
    architecture_decisions: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    consistency_warnings: list[str] = Field(
        default_factory=list,
        description=(
            "Heuristic tension checks (input vs stated scale, stack, budget, etc.) plus optional "
            "[Diagram] hints when Mermaid text looks structurally off. Not exhaustive; false positives/negatives are possible."
        ),
    )


class CreateDesignRequest(BaseModel):
    input: DesignInputPayload
    scale_stance: ScaleStance = "balanced"
    output_language: str = Field(default="en", max_length=5, description="ISO language code for AI output (en, tr, de)")


class DesignSummary(BaseModel):
    id: int
    title: str
    project_type: str
    status: str
    notes: str
    created_at: datetime
    updated_at: datetime


class DesignDetailResponse(BaseModel):
    id: int
    title: str
    project_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    notes: str
    discussion_conversation_id: int | None = None
    input: DesignInputPayload
    output: DesignOutputPayload | None = None
    share_enabled: bool = False
    share_url: str | None = None


class DesignShareStatusResponse(BaseModel):
    enabled: bool
    share_url: str | None = None


class PublicDesignResponse(BaseModel):
    """Read-only design artifact for unauthenticated share links (no private notes)."""

    id: int
    title: str
    project_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    input: DesignInputPayload
    output: DesignOutputPayload | None = None


class RegenerateDesignRequest(BaseModel):
    scale_stance: ScaleStance = "balanced"
    output_language: str = Field(default="en", max_length=5, description="ISO language code for AI output (en, tr, de)")


class RegenerateDesignResponse(BaseModel):
    design_id: int
    status: str
    message: str


class DesignVersionSummary(BaseModel):
    id: int
    created_at: datetime
    model_name: str
    generation_ms: int
    scale_stance: str


class DesignVersionDetail(BaseModel):
    id: int
    design_id: int
    created_at: datetime
    model_name: str
    generation_ms: int
    scale_stance: str
    output: DesignOutputPayload


class DesignVersionCompareResponse(BaseModel):
    version_a_id: int
    version_b_id: int
    diff_markdown: str


class ExportResponse(BaseModel):
    design_id: int
    title: str
    format: str
    content: str


class CostAnalysisRequest(BaseModel):
    traffic_multiplier: float = Field(default=1.0, ge=0.25, le=20.0)
    data_multiplier: float = Field(default=1.0, ge=0.25, le=20.0)
    reliability_profile: Literal["lean", "balanced", "critical"] = "balanced"


class CostAnalysisResponse(BaseModel):
    design_id: int
    monthly_usd_min: int
    monthly_usd_max: int
    yearly_usd_min: int
    yearly_usd_max: int
    confidence: Literal["low", "medium", "high"]
    breakdown: list[str]
    optimization_recommendations: list[str]


class ExportJobCreateResponse(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]


class ExportJobStatusResponse(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    format: Literal["pdf", "markdown"] | None = None
    filename: str | None = None
    error: str | None = None


class PaginatedDesignSummaryResponse(BaseModel):
    items: list[DesignSummary]
    total: int
    page: int
    page_size: int


class UpdateDesignNotesRequest(BaseModel):
    notes: str = Field(max_length=5000)


class UpdateDesignArchitectureRequest(BaseModel):
    mermaid: str = Field(min_length=1, max_length=50000)


class UpdateDesignNotesResponse(BaseModel):
    design_id: int
    notes: str
    updated_at: datetime


class DesignReviewStatusResponse(BaseModel):
    design_id: int
    review_status: Literal["draft", "in_review", "approved", "changes_requested"]
    review_owner_user_id: int | None = None
    reviewed_at: datetime | None = None
    review_decision_note: str = ""


class UpdateDesignReviewRequest(BaseModel):
    review_status: Literal["draft", "in_review", "approved", "changes_requested"]
    review_owner_user_id: int | None = None
    review_decision_note: str = Field(default="", max_length=2000)


class DesignCommentOut(BaseModel):
    id: int
    design_id: int
    user_id: int | None = None
    author_name: str | None = None
    content: str
    created_at: datetime


class CreateDesignCommentRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class CostCalibrationResponse(BaseModel):
    design_id: int
    estimated_monthly_usd_min: int
    estimated_monthly_usd_max: int
    calibrated_monthly_usd_min: int
    calibrated_monthly_usd_max: int
    calibration_factor: float
    confidence: Literal["low", "medium", "high"]
