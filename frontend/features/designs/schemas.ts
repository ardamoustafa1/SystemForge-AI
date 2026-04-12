import { z } from "zod";

export const createDesignSchema = z.object({
  project_title: z.string().trim().min(3, "Project title must be at least 3 characters"),
  project_type: z.string().trim().min(2, "Project category is required"),
  problem_statement: z.string().trim().min(20, "Project description should be at least 20 characters"),
  expected_users: z.string().trim().min(1, "Expected users is required"),
  traffic_assumptions: z.string().trim().min(1, "Traffic assumptions are required"),
  budget_sensitivity: z.enum(["low", "medium", "high"]),
  preferred_stack: z.string().trim().optional(),
  constraints: z.string().trim().min(1, "Constraints are required"),
  deployment_scope: z.enum(["single-region", "multi-region", "global"]),
  data_sensitivity: z.enum(["low", "medium", "high", "critical"]),
  real_time_required: z.boolean(),
  mode: z.enum(["interview", "product"]),
  scale_stance: z.enum(["balanced", "conservative", "aggressive"]),
});
