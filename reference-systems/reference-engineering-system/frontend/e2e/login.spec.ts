import { test, expect } from "@playwright/test";
import { login } from "./helpers";

test.describe("login", () => {
  test("valid credentials reach the dashboard and set the session", async ({ page }) => {
    await login(page);
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
    await expect(page.getByText("Meridian Tower").first()).toBeVisible();
  });

  test("invalid credentials show an error and stay on the login page", async ({ page }) => {
    await page.goto("/login");
    await page.locator("#email").fill("ananya.rao@meridiangc.example");
    await page.locator("#password").fill("wrong-password");
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(page.getByText(/invalid email or password/i)).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test("an unauthenticated visit to a project page redirects to login", async ({ page }) => {
    await page.goto("/projects/1/schedule");
    await expect(page).toHaveURL(/\/login/);
  });
});
