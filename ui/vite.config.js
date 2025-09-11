import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  esbuild: {
    // Only remove console in actual deployment (keep for local debugging)
    drop: process.env.RENDER === 'true' ? ['console', 'debugger'] : []
  },
  server: {
    proxy: {
      '/signals': 'http://127.0.0.1:8000',
      '/controls': 'http://127.0.0.1:8000',
      '/map': 'http://127.0.0.1:8000',
      '/products': 'http://127.0.0.1:8000',
      '/trend': 'http://127.0.0.1:8000',
      '/debug': 'http://127.0.0.1:8000',
      '/top_signals': 'http://127.0.0.1:8000',
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Core React libraries
          vendor: ['react', 'react-dom'],
          // Chart visualization library (large dependency)
          echarts: ['echarts', 'echarts-for-react']
        }
      }
    },
    // Suppress chunk size warning since we're intentionally splitting
    chunkSizeWarningLimit: 600
  }
})
