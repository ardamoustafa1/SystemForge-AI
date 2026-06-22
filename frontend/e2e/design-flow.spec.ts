import { test, expect } from "@playwright/test";
import { signInDemo } from "./helpers";

test.describe("Design Creation and Export Flow", () => {
  test.beforeEach(async ({ page }) => {
    await signInDemo(page);
  });

  test("should create a design, wait for generation, and verify export options", async ({
    page,
  }) => {
    // 1. Create a Design
    await page.goto("/dashboard/new");
    await page.fill('input[name="project_title"]', "E2E Test Architecture");
    await page.fill(
      'textarea[name="problem_statement"]',
      "We need a highly scalable microservices architecture for an E2E test.",
    );
    await page.click('button[type="submit"]');

    // 2. Wait for generation to complete (simulated wait)
    // In a real scenario we wait for the websocket or status to change to 'completed'
    await expect(page.locator("text=E2E Test Architecture")).toBeVisible({
      timeout: 15000,
    });

    // We expect the artifact viewer to render
    await expect(page.locator(".markdown-body")).toBeVisible({
      timeout: 60000,
    });

    // 3. Verify Export Options
    await page.click('text="Export"');

    // Expect download options to be present
    await expect(page.locator('text="Download PDF"')).toBeVisible();
    await expect(page.locator('text="Download Markdown"')).toBeVisible();
    await expect(page.locator('text="Terraform IaC"')).toBeVisible();
  });

  test("should view a public share link", async ({ page, context }) => {
    // Navigate to a known design
    await page.goto("/dashboard");
    await page.locator('text="SaaS Control Plane"').first().click(); // Open demo seed design

    // Get Share link
    await page.click('text="Share"');
    await page.click('text="Enable Public Link"'); // If exists

    const shareUrl = await page.inputValue('input[name="share_link"]');

    // Open in incognito context to verify public viewing
    const incognitoContext = await context.browser()?.newContext();
    const incognitoPage = await incognitoContext!.newPage();

    await incognitoPage.goto(shareUrl);
    await expect(
      incognitoPage.locator('text="SaaS Control Plane"'),
    ).toBeVisible();
    await incognitoPage.close();
  });
});
