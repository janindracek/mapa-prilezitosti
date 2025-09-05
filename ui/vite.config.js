import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
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
  }
})
