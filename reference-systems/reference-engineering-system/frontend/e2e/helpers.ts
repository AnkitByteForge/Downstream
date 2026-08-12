import { expect, type Page } from "@playwright/test";

export const DEMO_PASSWORD = "downstream-demo";
export const ANANYA_EMAIL = "ananya.rao@meridiangc.example";

export async function login(page: Page, email: string = ANANYA_EMAIL, password: string = DEMO_PASSWORD) {
  await page.goto("/login");
  await page.locator("#email").fill(email);
  await page.locator("#password").fill(password);
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page).toHaveURL(/\/dashboard/);
}
