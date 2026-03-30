import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Use 127.0.0.1 so the dev proxy always hits IPv4; `localhost` can resolve to ::1
// while the API may only listen on 127.0.0.1, which breaks every request on some Windows setups.
const apiProxyTarget =
  process.env.VITE_DEV_API_TARGET || 'http://127.0.0.1:8000'

const apiProxy = {
  '/api': {
    target: apiProxyTarget,
    changeOrigin: true,
    secure: false,
    rewrite: (path) => path.replace(/^\/api/, ''),
  },
}

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    // Listen on all interfaces so LAN / hostname access still hits the proxy
    host: true,
    proxy: apiProxy,
  },
  preview: {
    port: 4173,
    host: true,
    proxy: apiProxy,
  },
})
