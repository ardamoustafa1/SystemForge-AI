import { test, expect } from "@playwright/test";

import { signInDemo } from "./helpers";

test.describe("Full System Flow", () => {
  test("creates and opens a schema-valid architecture artifact", async ({ page, browserName }) => {
    test.skip(browserName !== "chromium", "Mutation smoke runs once; read-only flows cover the browser matrix.");

    await signInDemo(page);
    await page.goto("/dashboard/new");

    await page.getByRole("textbox", { name: "Project Title" }).fill(`E2E Architecture ${Date.now()}`);
    await page.getByRole("textbox", { name: "Project Category" }).fill("B2B SaaS");
    await page
      .getByRole("textbox", { name: "Project Description / Problem Statement" })
      .fill("Design a tenant-safe architecture artifact for the automated end-to-end release gate.");
    await page.getByRole("button", { name: "B2B SaaS baseline" }).click();

    await page.getByRole("button", { name: "Next" }).click();
    await expect(page.getByRole("textbox", { name: "Expected Users" })).toBeVisible();
    await page.getByRole("button", { name: "Next" }).click();
    await page.getByRole("textbox", { name: "Preferred Stack" }).fill("Next.js, FastAPI, PostgreSQL, Redis");
    await page
      .getByRole("textbox", { name: "Constraints" })
      .fill("Workspace isolation, idempotent jobs, audit logs, and deterministic fallback output.");

    await page.getByRole("button", { name: "Generate Architecture Package" }).click();
    await expect(page).toHaveURL(/\/dashboard\/designs\/\d+/, { timeout: 30_000 });
    await expect(page.getByText("Architecture Review Document")).toBeVisible();
    await expect(page.getByRole("button", { name: "Download PDF" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Executive Summary" })).toBeVisible();
  });
});
