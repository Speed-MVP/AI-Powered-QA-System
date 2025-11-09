import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  // Development optimizations
  server: {
    hmr: {
      overlay: true,
    },
  },
  // Build optimizations for production
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
        },
      },
    },
    // Disable source maps in production for better performance and security
    // Vite sets NODE_ENV during build, so this will work correctly
    sourcemap: false,
    // Optimize chunk size
    chunkSizeWarningLimit: 1000,
  },
  // Optimize dependencies for faster dev server
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom'],
  },
})
