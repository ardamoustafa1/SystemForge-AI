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
  output: DesignOutput;
  share_enabled?: boolean;
  share_url?: string | null;
};
