import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    // Dev only: forward API calls to the Flask container published on localhost:5000.
    // The browser talks to one origin, so there is no CORS to configure.
    // In production Nginx does the same job.
    proxy: {
      "/api": "http://localhost:5000",
    },
  },
});
