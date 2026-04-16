from pydantic import BaseModel


class OpsSummaryResponse(BaseModel):
    total_designs: int
    generating_count: int
    approved_count: int
    review_pending_count: int
    avg_generation_ms: int
    monthly_cost_min_total: int
    monthly_cost_max_total: int
    risk_drift_count: int

