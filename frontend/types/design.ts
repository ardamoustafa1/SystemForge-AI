export type Scorecard = {
  scalability: number;
  reliability: number;
  security: number;
  maintainability: number;
  cost_efficiency: number;
  simplicity: number;
  biggest_risk: string;
  biggest_bottleneck: string;
  first_optimization: string;
  avoid_overengineering: string;
};

export type EstimatedCloudCost = {
  monthly_usd_min: number;
  monthly_usd_max: number;
  cost_breakdown: string[];
};

export type DesignOutput = {
  executive_summary: string;
  assumptions?: string[];
  architecture_decisions?: string[];
  open_questions?: string[];
  consistency_warnings?: string[];
  functional_requirements: string[];
  non_functional_requirements: string[];
  high_level_architecture: string;
  core_components: string[];
  data_layer_recommendations: string[];
  cache_strategy: string;
  queue_event_strategy: string;
  api_service_design_notes: string[];
  scalability_plan: string[];
  reliability_and_failure_points: string[];
  security_considerations: string[];
  cost_considerations: string[];
  tradeoff_decisions: string[];
  recommended_implementation_phases: string[];
  engineering_checklist: string[];
  architecture_scorecard: Scorecard;
  estimated_cloud_cost?: EstimatedCloudCost | null;
  suggested_mermaid_diagram: string;
  final_recommendation: string;
};

export type DesignRecord = {
  id: number;
  title: string;
  project_type: string;
  status: string;
  created_at: string;
  updated_at: string;
  notes: string;
  /** Realtime messaging thread; distinct from design id. */
  discussion_conversation_id?: number | null;
  input: Record<string, unknown>;
  output: DesignOutput | null;
  share_enabled?: boolean;
  share_url?: string | null;
  review_status?: "draft" | "in_review" | "approved" | "changes_requested";
  review_owner_user_id?: number | null;
  review_decision_note?: string;
  reviewed_at?: string | null;
};

export type GenerationProgress = {
  design_id: number;
  status: string;
  phase?: string;
  progress_pct?: number;
  trace_id?: string;
};

export type CostAnalysisResult = {
  design_id: number;
  monthly_usd_min: number;
  monthly_usd_max: number;
  yearly_usd_min: number;
  yearly_usd_max: number;
  confidence: "low" | "medium" | "high";
  breakdown: string[];
  optimization_recommendations: string[];
};

export type DesignReview = {
  design_id: number;
  review_status: "draft" | "in_review" | "approved" | "changes_requested";
  review_owner_user_id?: number | null;
  reviewed_at?: string | null;
  review_decision_note: string;
};

export type DesignComment = {
  id: number;
  design_id: number;
  user_id?: number | null;
  author_name?: string | null;
  content: string;
  created_at: string;
};

export type OpsSummary = {
  total_designs: number;
  generating_count: number;
  approved_count: number;
  review_pending_count: number;
  avg_generation_ms: number;
  monthly_cost_min_total: number;
  monthly_cost_max_total: number;
  risk_drift_count: number;
};

export type CostCalibration = {
  design_id: number;
  estimated_monthly_usd_min: number;
  estimated_monthly_usd_max: number;
  calibrated_monthly_usd_min: number;
  calibrated_monthly_usd_max: number;
  calibration_factor: number;
  confidence: "low" | "medium" | "high";
};
