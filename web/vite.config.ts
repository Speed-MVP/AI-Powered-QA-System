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
          'react-vendor': ['react', 'react-dom'],
          'router-vendor': ['react-router-dom'],
          'ui-vendor': ['lucide-react', 'react-icons'],
        },
      },
    },
    // Disable source maps in production for better performance and security
    sourcemap: false,
    // Optimize chunk size
    chunkSizeWarningLimit: 1000,
    // Enable minification
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
    // Preload modules for better performance
    modulePreload: {
      polyfill: false,
    },
  },
  // Optimize dependencies for faster dev server
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom'],
  },
})
