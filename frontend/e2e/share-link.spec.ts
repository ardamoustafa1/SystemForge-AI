import { test, expect } from "@playwright/test";

test.describe("Share Link Access", () => {
  test("Public share link displays design readonly", async ({ page }) => {
    // 1. Mock public design endpoint
    await page.route("/api/public/share/test-token-123", async (route) => {
      await route.fulfill({
        json: {
          id: 10,
          title: "Public Shared Design",
          mode: "product",
          output: { core_components: ["shared-auth"] },
        },
      });
    });

    // 2. Navigate to public share URL
    await page.goto("/share/test-token-123");

    // 3. Verify page content
    await expect(page.getByText("Public Shared Design")).toBeVisible();

    // 4. Verify no edit controls are present
    await expect(
      page.getByRole("button", { name: /save changes/i }),
    ).not.toBeVisible();
    await expect(
      page.getByRole("button", { name: /regenerate/i }),
    ).not.toBeVisible();
  });

  test("Invalid share link shows 404 state", async ({ page }) => {
    await page.route("/api/public/share/invalid-token", async (route) => {
      await route.fulfill({ status: 404 });
    });

    await page.goto("/share/invalid-token");
    await expect(page.getByText(/not found/i)).toBeVisible();
  });
});
