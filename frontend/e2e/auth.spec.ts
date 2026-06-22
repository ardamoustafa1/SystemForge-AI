import { test, expect } from "@playwright/test";

test.describe("Authentication Flow", () => {
  const randomSuffix = Math.floor(Math.random() * 1000000);
  const testEmail = `testuser_${randomSuffix}@example.com`;
  const testPassword = "StrongPassword123!";

  test("Complete Auth Cycle: Register -> Login -> Logout", async ({ page }) => {
    // 1. Navigate to Sign Up
    await page.goto("/auth/sign-up");

    // 2. Register User
    await page.fill('input[name="full_name"]', "Test User");
    await page.fill('input[name="email"]', testEmail);
    await page.fill('input[name="password"]', testPassword);

    await Promise.all([
      page.waitForURL(/.*dashboard.*/),
      page.click('button[type="submit"]'),
    ]);

    await expect(page).toHaveURL(/.*dashboard.*/);

    // 3. Logout
    await page.click('button[aria-label="User menu"]'); // Assuming there's a user menu
    await Promise.all([
      page.waitForURL(/.*sign-in.*/),
      page.click('text="Log out"'), // Assuming a logout button
    ]);

    await expect(page).toHaveURL(/.*sign-in.*/);

    // 4. Login Again
    await page.fill('input[name="email"]', testEmail);
    await page.fill('input[name="password"]', testPassword);

    await Promise.all([
      page.waitForURL(/.*dashboard.*/),
      page.click('button[type="submit"]'),
    ]);

    await expect(page).toHaveURL(/.*dashboard.*/);
  });
});
