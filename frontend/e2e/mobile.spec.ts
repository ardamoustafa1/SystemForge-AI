import { test, expect, devices } from "@playwright/test";
import { signInDemo } from "./helpers";

test.use({
  ...devices["iPhone 13"],
});

test.describe("Mobile Viewport Layouts", () => {
  test("dashboard and navigation work on mobile", async ({ page }) => {
    await signInDemo(page);

    await page.goto("/dashboard");

    // Wait for dashboard to load
    await expect(page.locator("main")).toBeVisible();

    // The grid should adapt to the mobile viewport, meaning items stack
    const designCards = page.locator('a[href^="/dashboard/designs/"]');
    if ((await designCards.count()) > 0) {
      const box = await designCards.first().boundingBox();
      // On iPhone 13, viewport width is 390
      expect(box?.width).toBeLessThanOrEqual(390);
    }
  });
});
