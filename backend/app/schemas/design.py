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


class PaginatedDesignSummaryResponse(BaseModel):
    items: list[DesignSummary]
    total: int
    page: int
    page_size: int


class UpdateDesignNotesRequest(BaseModel):
    notes: str = Field(max_length=5000)


class UpdateDesignNotesResponse(BaseModel):
    design_id: int
    notes: str
    updated_at: datetime
