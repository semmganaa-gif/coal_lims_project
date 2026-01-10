import { defineConfig } from 'vite'
import { resolve } from 'path'

export default defineConfig({
  // Development server тохиргоо
  server: {
    port: 5173,
    // Flask dev server-тэй proxy холболт
    proxy: {
      '/api': 'http://localhost:5000',
      '/static': 'http://localhost:5000',
    },
  },

  // Build тохиргоо
  build: {
    // Flask static folder руу гаргах
    outDir: 'app/static/dist',
    emptyOutDir: true,

    // Manifest file - Flask-д ашиглах
    manifest: true,

    rollupOptions: {
      input: {
        // Main entry points
        main: resolve(__dirname, 'src/main.js'),
        // Тусдаа bundle-ууд (шаардлагатай бол)
        // analysis: resolve(__dirname, 'src/analysis.js'),
      },
      output: {
        // Asset naming
        entryFileNames: 'js/[name]-[hash].js',
        chunkFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          if (assetInfo.name?.endsWith('.css')) {
            return 'css/[name]-[hash][extname]'
          }
          return 'assets/[name]-[hash][extname]'
        },
      },
    },
  },

  // Resolve тохиргоо
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
})
