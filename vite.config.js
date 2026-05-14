import { defineConfig } from 'vite'
import { resolve } from 'path'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [tailwindcss()],

  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:5000',
      '/static': 'http://localhost:5000',
    },
  },

  build: {
    outDir: 'app/static/dist',
    emptyOutDir: true,
    manifest: true,

    rollupOptions: {
      input: {
        main: resolve(__dirname, 'src/main.js'),
        styles: resolve(__dirname, 'src/styles.css'),
        aggrid: resolve(__dirname, 'src/aggrid.js'),
        'aggrid-css': resolve(__dirname, 'src/aggrid.css'),
        chart: resolve(__dirname, 'src/chart.js'),
      },
      output: {
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

  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
})
