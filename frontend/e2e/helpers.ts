import { expect, type Page } from "@playwright/test";

export async function signInDemo(page: Page) {
  await page.goto("/auth/sign-in");
  await page.getByRole("textbox", { name: "Email" }).fill("demo@systemforge.dev");
  await page.getByRole("textbox", { name: "Password" }).fill("SystemForgeDemo123!");
  await page.getByRole("button", { name: "Sign In" }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole("heading", { name: "Design Workspace" })).toBeVisible();
}
