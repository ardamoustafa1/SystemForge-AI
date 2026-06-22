import { test, expect } from "@playwright/test";

import { signInDemo } from "./helpers";

test.describe("Settings Page", () => {
  test.beforeEach(async ({ page }) => {
    await signInDemo(page);
    await page.goto("/dashboard/settings");
    await expect(page.getByRole("heading", { name: "Settings" })).toBeVisible();
  });

  test("displays the demo user profile", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Personal Information" })).toBeVisible();
    await expect(page.locator('input[value="SystemForge Demo"]')).toBeVisible();
    await expect(page.locator('input[value="demo@systemforge.dev"]')).toBeVisible();
  });

  test("asks for confirmation before account deletion", async ({ page }) => {
    page.once("dialog", async (dialog) => {
      expect(dialog.message()).toContain("Are you sure you want to delete your account?");
      await dialog.dismiss();
    });
    await page.getByRole("button", { name: "Delete Account" }).click();
  });

  test("shows a newly generated API key once", async ({ page }) => {
    await page.route("**/api/auth/api-keys", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({ json: { api_key: "sf_e2e_example_secret_key_1234" } });
        return;
      }
      await route.fulfill({ json: { last4: null, created_at: null, revoked_at: null } });
    });

    await page.getByRole("button", { name: "API Keys" }).click();
    await page.getByRole("button", { name: "Generate Secret Key" }).click();
    await expect(page.getByRole("heading", { name: "Your New API Key" })).toBeVisible();
    await expect(page.getByText("sf_e2e_example_secret_key_1234")).toBeVisible();
    await page.getByRole("button", { name: "I have copied it" }).click();
    await expect(page.getByRole("heading", { name: "Your New API Key" })).toBeHidden();
  });
});
