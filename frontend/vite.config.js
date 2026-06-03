import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: ['pumpr.zeolite'],
    host: '0.0.0.0',
  },
  define: {
    'import.meta.env.VITE_BUILD_HASH': JSON.stringify(process.env.BUILD_HASH || 'dev'),
  },
})
