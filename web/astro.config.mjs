// @ts-check
import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  site: "https://www.orflaedi.is",
  vite: { plugins: [tailwindcss()] },
});
