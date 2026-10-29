import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// O front chama `/api/...`; o Vite repassa para a API local removendo o prefixo.
// Isso evita CORS. Para outra URL da API: VITE_API_TARGET=http://host:porta
const target = process.env.VITE_API_TARGET || "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target, changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, "") },
    },
  },
});
