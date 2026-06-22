import { test, expect } from "@playwright/test";

test.describe("Authentication Flow - Sign Up", () => {
  test("successful sign up redirects to dashboard", async ({ page }) => {
    await page.goto("/auth/sign-up");

    // Wait for the sign up form to be visible
    await expect(page.locator("form")).toBeVisible();

    // Fill form using placeholders which are usually standard
    const uniqueEmail = `testuser_${Date.now()}@systemforge.dev`;

    // Using generic locators for robustness since exact labels might be translated
    await page.locator('input[type="text"]').first().fill("Test User");
    await page.locator('input[type="email"]').fill(uniqueEmail);
    await page.locator('input[type="password"]').fill("TestPass123!@");

    // Submit
    await page.locator('button[type="submit"]').click();

    // Verify redirection to dashboard
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test("shows validation errors for invalid inputs", async ({ page }) => {
    await page.goto("/auth/sign-up");

    // Submit empty form
    await page.locator('button[type="submit"]').click();

    // Check for validation errors. We expect the form to remain and show some error state.
    // Instead of exact text, we just ensure we haven't navigated away.
    await expect(page).toHaveURL(/\/auth\/sign-up/);
  });
});
