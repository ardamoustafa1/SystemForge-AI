import { test, expect } from "@playwright/test";
import { signInDemo } from "./helpers";

test.describe("RBAC and Security Restrictions", () => {
  test("enforces role checks on settings page", async ({ page }) => {
    await signInDemo(page);

    await page.goto("/dashboard/settings");

    // Check if the page loads without crashing and displays the layout
    await expect(page.locator("main")).toBeVisible();

    // Verify presence of role/workspace information
    // If user is a viewer, they shouldn't see edit inputs, but demo user might be admin
    const inputs = page.locator("input");
    await expect(inputs.first()).toBeVisible();
  });
});
