import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  // Read the shared .env at the repo root.
  const env = loadEnv(mode, "..", "");
  return {
    plugins: [react()],
    envDir: "..",
    server: {
      port: 5173,
      // Forward /api to FastAPI so the browser talks to one origin in development.
      proxy: { "/api": env.VITE_API_PROXY_TARGET || "http://localhost:8000" },
    },
  };
});
