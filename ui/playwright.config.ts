import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  use: { baseURL: "http://localhost:4173", viewport: { width: 1440, height: 900 } },
  webServer: { command: "npx vite preview --port 4173 --strictPort", port: 4173, reuseExistingServer: true },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
});
