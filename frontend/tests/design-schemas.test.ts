import { describe, expect, it } from "vitest";

import { createDesignSchema } from "@/features/designs/schemas";

describe("create design schema", () => {
  it("accepts valid design payload", () => {
    const parsed = createDesignSchema.safeParse({
      project_title: "SystemForge Messaging Platform",
      project_type: "chat",
      problem_statement: "Design a scalable chat backend and architecture artifact platform.",
      expected_users: "1000000",
      traffic_assumptions: "peak 5000 rps",
      budget_sensitivity: "medium",
      preferred_stack: "fastapi,postgres,redis",
      constraints: "small team and fast launch",
      deployment_scope: "single-region",
      data_sensitivity: "medium",
      real_time_required: true,
      mode: "product",
    });
    expect(parsed.success).toBe(true);
  });

  it("rejects too-short project title", () => {
    const parsed = createDesignSchema.safeParse({
      project_title: "ab",
      project_type: "chat",
      problem_statement: "Design a scalable chat backend and architecture artifact platform.",
      expected_users: "1000000",
      traffic_assumptions: "peak 5000 rps",
      budget_sensitivity: "medium",
      preferred_stack: "fastapi,postgres,redis",
      constraints: "small team and fast launch",
      deployment_scope: "single-region",
      data_sensitivity: "medium",
      real_time_required: true,
      mode: "product",
    });
    expect(parsed.success).toBe(false);
  });
});
