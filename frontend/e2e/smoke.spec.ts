import { test, expect } from "@playwright/test";

test.describe("Smoke", () => {
  test("landing page loads with expected title", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/SystemForge/i);
  });

  test("health-related route responds", async ({ page }) => {
    const res = await page.goto("/");
    expect(res?.ok()).toBeTruthy();
  });
});
