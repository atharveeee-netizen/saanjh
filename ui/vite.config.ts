import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";

// `--mode artifact` inlines all JS and CSS into one HTML file for static hosting;
// the data JSON in public/data is published next to it.
export default defineConfig(({ mode }) => ({
  base: "./",
  plugins: [react(), ...(mode === "artifact" ? [viteSingleFile()] : [])],
  build: { outDir: mode === "artifact" ? "dist-artifact" : "dist", chunkSizeWarningLimit: 1500 },
  server: { port: 5173 },
}));
