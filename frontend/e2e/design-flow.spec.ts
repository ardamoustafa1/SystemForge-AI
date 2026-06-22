import { test, expect } from "@playwright/test";

import { signInDemo } from "./helpers";

test.describe("Design Generation Flow", () => {
  test("shows the seeded dashboard and current design form", async ({ page }) => {
    await signInDemo(page);

    await expect(page.getByText("Multi-tenant SaaS Control Plane")).toBeVisible();
    await expect(page.getByText("Marketplace Order & Fulfillment Platform")).toBeVisible();
    await expect(page.getByText("AI Workflow Automation Hub")).toBeVisible();

    await page.goto("/dashboard/new");
    await expect(page.getByRole("heading", { name: "Create New System Design" })).toBeVisible();
    await expect(page.getByRole("textbox", { name: "Project Title" })).toBeVisible();
    await expect(page.getByRole("textbox", { name: "Project Category" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Generate Architecture Package" })).toBeVisible();
  });
});
