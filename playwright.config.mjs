import path from "node:path";
import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "tests",
  testMatch: "browser.spec.mjs",
  workers: 1,
  use: {
    launchOptions: { downloadsPath: path.resolve("test-results/downloads") },
    baseURL: "http://127.0.0.1:8767",
    locale: "en-US",
    timezoneId: "UTC",
    viewport: { width: 1440, height: 900 },
  },
  webServer: {
    command:
      "python3 -m http.server 8767 --bind 127.0.0.1 --directory examples/business-review",
    url: "http://127.0.0.1:8767",
    reuseExistingServer: false,
  },
});
