import { test, expect } from "@playwright/test";
import { signInDemo } from "./helpers";

test.describe("Design Creation Flow", () => {
  test("creates a new design and waits for generation", async ({ page }) => {
    await signInDemo(page);

    await page.goto("/dashboard/new");

    // Wait for the form
    await expect(page.locator("form")).toBeVisible();

    // Fill project details using generic index-based or type-based locators to bypass i18n
    const inputs = page.locator('input[type="text"]');
    await inputs.nth(0).fill("Test E2E Architecture");
    await inputs.nth(1).fill("E-commerce");

    const textarea = page.locator("textarea");
    await textarea.fill("Must handle 10k users per minute with 99.99% uptime.");

    // Submit form
    await page.locator('button[type="submit"]').click();

    // Verify it redirects to the design detail page
    await expect(page).toHaveURL(/\/dashboard\/designs\/\d+/);

    // Wait for the generation to complete (timeout increased to allow LLM processing)
    // We expect the main content to load
    await expect(page.locator("main")).toBeVisible({ timeout: 60000 });
  });
});
