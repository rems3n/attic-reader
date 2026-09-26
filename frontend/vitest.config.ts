import { defineConfig } from "vitest/config";

// tsconfig keeps "jsx": "preserve" for Next.js; tests that render components
// (lib/diagrams.test.ts) need the automatic JSX runtime instead.
export default defineConfig({
  esbuild: { jsx: "automatic" },
});
