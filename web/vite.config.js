import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  base: '/idaho_mfg',
  plugins: [react(), tailwindcss()],
  build: {
    chunkSizeWarningLimit: 2_000, // 2 MB, index is ~1.5 MB
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          if (id.includes("node_modules")) {
            return "vendor"
          } else if (id.endsWith(".json")) {
            const parts = id.split("/")
            return parts[parts.length -1] // return JSON file name as chunk
          }
          return "app"
        }
      }
    }
  }
})
