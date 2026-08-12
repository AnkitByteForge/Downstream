import { defineConfig, devices } from "@playwright/test";

// RES-5: the first browser-automation suite for the Reference Engineering
// System frontend, explicitly deferred by every prior RES milestone (§10.6,
// §11.9, §16). Assumes the backend (port 8000) and frontend dev server
// (port 3100) are already running against a seeded Meridian Tower database —
// this suite reads the canonical seed, it does not create its own fixtures,
// matching how every other RES verification pass has used the one seed.
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:3100",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
