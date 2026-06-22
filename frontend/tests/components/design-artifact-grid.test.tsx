import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { DesignArtifactGrid } from "../../components/design/design-artifact-grid";

// Mock the dynamic ArchitectureCanvas to prevent JSDom canvas issues
vi.mock("@/components/design/architecture-canvas", () => ({
  ArchitectureCanvas: () => (
    <div data-testid="architecture-canvas">Canvas Mock</div>
  ),
}));

// Mock the API client
vi.mock("@/lib/api", () => ({
  api: vi.fn(),
}));

const mockData = {
  id: 1,
  workspace_id: 1,
  project_title: "Test Architecture",
  project_category: "E-commerce",
  business_requirements: "Fast",
  status: "approved",
  output: {
    executive_summary: "This is a great architecture.",
    high_level_architecture: "Microservices",
    architecture_scorecard: {
      scalability: 8,
      reliability: 9,
      security: 7,
      maintainability: 8,
      cost_efficiency: 7,
      simplicity: 6,
      biggest_risk: "Complexity",
      biggest_bottleneck: "DB",
      first_optimization: "Cache",
      avoid_overengineering: "Keep it simple",
    },
    runtime_topology: {
      architecture_style: "Event Driven",
      deployable_units: ["App", "Worker"],
      primary_runtime_paths: ["User -> App"],
      stateful_components: ["DB"],
    },
    data_flows: {
      request_response_flow: [],
      asynchronous_event_flow: [],
      persistence_flow: [],
      failure_recovery_flow: [],
    },
    websocket_architecture: {
      pubsub_backplane: "",
      sticky_session_strategy: "",
      connection_lifecycle: [],
      fanout_strategy: [],
      scaling_strategy: [],
      channel_partitioning: [],
      shard_strategy: [],
      topic_design: [],
      partition_keys: [],
    },
    video_streaming_architecture: {
      streaming_protocols: [],
      ingest_and_packaging: [],
      cdn_strategy: [],
      adaptive_bitrate_strategy: [],
    },
    database_architecture: {
      primary_entities: [],
      schema_design: [],
      indexing_strategy: [],
      partitioning_strategy: [],
    },
    observability_architecture: {
      logging_strategy: [],
      tracing_strategy: [],
      metrics_strategy: [],
      alerting_strategy: [],
      sli_slo_targets: [],
    },
    ai_architecture: {
      request_guardrails: [],
      inference_orchestration: [],
      queue_and_backpressure: [],
      model_provider_strategy: [],
      fallback_and_recovery: [],
    },
    security_architecture: {
      auth_flow: [],
      session_and_refresh_flow: [],
      abuse_protection: [],
      secrets_and_key_management: [],
      audit_and_compliance: [],
    },
    functional_requirements: [],
    non_functional_requirements: [],
    tradeoff_decisions: [],
    engineering_checklist: ["Task 1", "Task 2"],
    suggested_mermaid_diagram: "graph TD; A-->B;",
  },
} as any;

describe("DesignArtifactGrid", () => {
  const mockT = (key: string) => key;

  it("renders executive summary and high level architecture", () => {
    render(<DesignArtifactGrid data={mockData} t={mockT} />);

    expect(
      screen.getByText("This is a great architecture."),
    ).toBeInTheDocument();
    expect(screen.getByText("Microservices")).toBeInTheDocument();
  });

  it("renders the scorecard correctly", () => {
    render(<DesignArtifactGrid data={mockData} t={mockT} />);

    expect(screen.getByText("detail.score.scalability")).toBeInTheDocument();
    expect(screen.getByText("8/10")).toBeInTheDocument();
    expect(screen.getByText("detail.score.reliability")).toBeInTheDocument();
    expect(screen.getByText("9/10")).toBeInTheDocument();
  });

  it("renders the dynamic architecture canvas", () => {
    render(<DesignArtifactGrid data={mockData} t={mockT} />);

    expect(screen.getByTestId("architecture-canvas")).toBeInTheDocument();
  });

  it("does not crash when optional properties are missing", () => {
    const minData = {
      ...mockData,
      output: { ...mockData.output, consistency_warnings: [] },
    };
    expect(() =>
      render(<DesignArtifactGrid data={minData} t={mockT} />),
    ).not.toThrow();
  });
});
