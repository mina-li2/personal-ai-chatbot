import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    // Windows + Docker bind mounts often fail to send proper file-change
    // events, so Vite's watcher misses edits. Polling checks files on an
    // interval instead, which is slightly less efficient but reliable.
    watch: {
      usePolling: true,
      interval: 300,
    },
  },
});