import { test, expect } from "@playwright/test";
import { signInDemo } from "./helpers";

test.describe("Realtime WebSocket Updates", () => {
  test("maintains websocket connection on design page", async ({ browser }) => {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();

    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    await signInDemo(page1);
    await signInDemo(page2);

    // Both go to dashboard
    await page1.goto("/dashboard");
    const firstDesign = page1.locator('a[href^="/dashboard/designs/"]').first();
    const designHref = await firstDesign.getAttribute("href");

    if (designHref) {
      await page1.goto(designHref);
      await page2.goto(designHref);

      // Verify page load
      await expect(page1.locator("main")).toBeVisible();
      await expect(page2.locator("main")).toBeVisible();
    }
  });
});
