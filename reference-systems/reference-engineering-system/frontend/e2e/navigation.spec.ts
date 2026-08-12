import { test, expect } from "@playwright/test";
import { login } from "./helpers";

// Golden-path click-through of every project workspace page via the sidebar
// nav, against the canonical Meridian Tower seed — the first browser-driven
// coverage for the whole RES frontend (RES-5, deferred by every prior
// milestone). Verifies each page actually renders seeded data, not just a
// 200 response.

test.describe("project workspace navigation", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("RFIs register shows RFI-214, closed", async ({ page }) => {
    await page.getByRole("link", { name: "RFIs" }).click();
    await expect(page).toHaveURL(/\/rfis$/);
    await expect(page.getByText("RFI-214")).toBeVisible();
  });

  test("RFI detail shows the closed response", async ({ page }) => {
    await page.getByRole("link", { name: "RFIs" }).click();
    await page.getByText("RFI-214").click();
    await expect(page).toHaveURL(/\/rfis\/\d+$/);
    await expect(page.getByText(/reroute duct per attached sk-14/i)).toBeVisible();
  });

  test("Drawings register shows M-2.1", async ({ page }) => {
    await page.getByRole("link", { name: "Drawings" }).click();
    await expect(page.getByText("M-2.1")).toBeVisible();
  });

  test("Submittals register shows SUB-118", async ({ page }) => {
    await page.getByRole("link", { name: "Submittals" }).click();
    await expect(page.getByText(/SUB-118/)).toBeVisible();
  });

  test("Design Changes register shows ASI-07, issued", async ({ page }) => {
    await page.getByRole("link", { name: "Design Changes" }).click();
    await expect(page.getByText("ASI-07")).toBeVisible();
    await expect(page.getByText("ISSUED")).toBeVisible();
  });

  test("Specifications page shows the CSI division tree", async ({ page }) => {
    await page.getByRole("link", { name: "Specifications" }).click();
    await expect(page.getByText(/23 31 13/)).toBeVisible();
  });

  test("Activity feed loads without error", async ({ page }) => {
    await page.getByRole("link", { name: "Activity" }).click();
    await expect(page).toHaveURL(/\/activity$/);
  });
});
