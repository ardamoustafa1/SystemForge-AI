import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should navigate to sign-in page', async ({ page }) => {
    await page.goto('/');
    
    // Check if the CTA button is visible
    const getStartedBtn = page.getByRole('link', { name: /start building/i }).first();
    if (await getStartedBtn.isVisible()) {
      await getStartedBtn.click();
    } else {
      await page.goto('/auth/sign-in');
    }

    // Ensure we reached the sign-in page
    await expect(page).toHaveURL(/.*sign-in|.*sign-up/);
    
    // Check for form elements using robust selectors
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
  });
});
