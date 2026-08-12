import { test, expect } from "@playwright/test";
import { login } from "./helpers";

// RES-5's own two register pages, against the canonical seed:
// ScheduleActivity (sched_3410, Canonical_Demo_Dataset.md §10/§13) and
// ModelObject (deliberately unseeded — ADR-008 §17.5).

test.describe("Schedule register", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.getByRole("link", { name: "Schedule" }).click();
    await expect(page).toHaveURL(/\/schedule$/);
  });

  test("shows the canonical sched_3410 activity with no invented data", async ({ page }) => {
    const row = page.getByRole("row").filter({ hasText: "3410" });
    await expect(row).toBeVisible();
    await expect(row).toContainText("procurement");
    // wbs was deliberately left null (ADR-008) — the row renders the em-dash
    // placeholder, not a fabricated WBS code.
    await expect(row).toContainText("—");
  });
});

test.describe("Model Objects register", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.getByRole("link", { name: "Model Objects" }).click();
    await expect(page).toHaveURL(/\/model-objects$/);
  });

  test("shows the empty state — no canonical ModelObject instance exists", async ({ page }) => {
    await expect(page.getByText(/no model objects on this project yet/i)).toBeVisible();
  });
});
