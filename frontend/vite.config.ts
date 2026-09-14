import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/health': 'http://localhost:8000',
      '/projects': 'http://localhost:8000',
      '/approvals': 'http://localhost:8000',
      '/obligations': 'http://localhost:8000',
      '/applications': 'http://localhost:8000',
    },
  },
})
