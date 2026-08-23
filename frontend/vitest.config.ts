import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

/**
 * Sprint 13 (Decision Workspace Product Integration) — the first test
 * tooling this frontend has; no test runner existed before this
 * sprint (confirmed: no `vitest`/`jest` config, no `*.test.*` file,
 * anywhere in the repository prior to this file). A separate config
 * from `vite.config.ts` (rather than merging `test` into it) so the
 * dev-server proxy config stays untouched and test-only concerns
 * don't leak into the app build.
 */
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/testSetup.ts"],
    globals: false,
  },
});
