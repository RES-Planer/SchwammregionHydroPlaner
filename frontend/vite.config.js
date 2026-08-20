import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // maplibre-gl ships its worker as a separate chunk that Vite's dependency
  // pre-bundler fails to resolve, breaking the map worker intermittently.
  optimizeDeps: {
    exclude: ['maplibre-gl'],
  },
  server: {
    // Proxy API calls through the dev server's own origin so the browser
    // never needs to reach the backend port directly (breaks under remote
    // port-forwarding, e.g. Codespaces/devcontainers, where "localhost"
    // in the browser resolves to the user's machine, not this container).
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
