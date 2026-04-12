import { test, expect } from "@playwright/test";

test.describe("Full System Flow", () => {
  test("creates a user, designs a system, and waits for async generation", async ({ page }) => {
    // 1. Signup
    await page.goto("/auth/sign-up");
    
    const randomUser = `test_e2e_${Date.now()}@example.com`;
    
    await page.fill("#full_name", "Test User");
    await page.fill("#email", randomUser);
    await page.fill("#password", "Password123!");
    await page.click('button[type="submit"]');
    
    // Wait for dashboard redirect
    await expect(page).toHaveURL(/\/dashboard/);
    
    // 2. Go to New Design
    await page.goto("/dashboard/new");
    await expect(page).toHaveURL(/\/dashboard\/new/);
    
    // Fill design context fields
    await page.fill("#project_title", "E2E Test Project");
    await page.fill("#project_type", "E-Commerce");
    await page.fill("#problem_statement", "A test architecture for e2e testing.");
    
    await page.fill("#expected_users", "1000");
    await page.fill("#traffic_assumptions", "100 RPS");
    
    await page.click('button[type="submit"]');
    
    // 3. Async Generation Wait
    // Redirection to design details page
    await expect(page).toHaveURL(/\/dashboard\/designs\/\d+/);
    
    // Check loading indicator displays due to initially "generating" status
    const generatingText = page.locator("text=Design is generating...");
    await expect(generatingText).toBeVisible({ timeout: 10000 });
    
    // 4. Polling wait (Wait for the LLM worker to complete the design)
    // We give it 60 seconds. In CI we might need more but this checks the polling mechanism.
    await expect(generatingText).toBeHidden({ timeout: 60000 });
    
    // 5. Verify the export buttons render properly confirming completion
    // The downloaded PDF icon button
    const pdfButton = page.locator('button:has(.lucide-file-down)');
    await expect(pdfButton.first()).toBeVisible();
    
    // The markdown copy button
    const markdownBtn = page.locator('button:has(.lucide-file-output)');
    await expect(markdownBtn.first()).toBeVisible();
  });
});
