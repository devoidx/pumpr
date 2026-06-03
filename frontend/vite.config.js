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
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('leaflet') || id.includes('react-leaflet')) return 'vendor-map'
            if (id.includes('recharts')) return 'vendor-charts'
            if (id.includes('@chakra-ui') || id.includes('@emotion') || id.includes('framer-motion')) return 'vendor-chakra'
            if (id.includes('react-dom') || id.includes('react-router')) return 'vendor-react'
            return 'vendor'
          }
        },
      },
    },
  },
})
