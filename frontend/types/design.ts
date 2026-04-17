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

export type RuntimeTopology = {
  architecture_style: string;
  deployable_units: string[];
  primary_runtime_paths: string[];
  stateful_components: string[];
};

export type DataFlows = {
  request_response_flow: string[];
  asynchronous_event_flow: string[];
  persistence_flow: string[];
  failure_recovery_flow: string[];
};

export type WebsocketArchitecture = {
  connection_lifecycle: string[];
  fanout_strategy: string[];
  scaling_strategy: string[];
  sticky_session_strategy: string;
  pubsub_backplane: string;
  channel_partitioning: string[];
  shard_strategy: string[];
  topic_design: string[];
  partition_keys: string[];
};

export type AIArchitecture = {
  request_guardrails: string[];
  inference_orchestration: string[];
  queue_and_backpressure: string[];
  model_provider_strategy: string[];
  fallback_and_recovery: string[];
};

export type SecurityArchitecture = {
  auth_flow: string[];
  session_and_refresh_flow: string[];
  abuse_protection: string[];
  secrets_and_key_management: string[];
  audit_and_compliance: string[];
};

export type VideoStreamingArchitecture = {
  streaming_protocols: string[];
  ingest_and_packaging: string[];
  cdn_strategy: string[];
  adaptive_bitrate_strategy: string[];
  realtime_interaction_sidecar: string[];
};

export type DatabaseArchitecture = {
  primary_entities: string[];
  schema_design: string[];
  indexing_strategy: string[];
  partitioning_strategy: string[];
  consistency_and_migration_notes: string[];
};

export type ObservabilityArchitecture = {
  logging_strategy: string[];
  tracing_strategy: string[];
  metrics_strategy: string[];
  alerting_strategy: string[];
  sli_slo_targets: string[];
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
  runtime_topology: RuntimeTopology;
  data_flows: DataFlows;
  websocket_architecture: WebsocketArchitecture;
  ai_architecture: AIArchitecture;
  security_architecture: SecurityArchitecture;
  video_streaming_architecture: VideoStreamingArchitecture;
  database_architecture: DatabaseArchitecture;
  observability_architecture: ObservabilityArchitecture;
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
