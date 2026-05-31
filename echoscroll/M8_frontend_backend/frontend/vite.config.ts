import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Vite dev server runs on :5173; the FastAPI backend on :8000.
// Proxy /api, /audio, /preview, /upload, /generate, /edit, /ws to the backend.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/upload":   "http://localhost:8000",
      "/generate": "http://localhost:8000",
      "/edit":     "http://localhost:8000",
      "/audio":    "http://localhost:8000",
      "/preview":  "http://localhost:8000",
      "/ws":       { target: "ws://localhost:8000", ws: true },
    },
  },
});
